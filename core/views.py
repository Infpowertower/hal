from django.shortcuts import render, redirect
from django.http import JsonResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
import json
import logging
from celery.result import AsyncResult
from .tasks import delete_ip_object
from .forms import DeleteIPObjectForm, UserLoginForm, UserRegistrationForm

logger = logging.getLogger(__name__)

# Authentication views
def login_view(request):
    """
    View for user login
    """
    if request.user.is_authenticated:
        return redirect('core:index')
        
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                next_url = request.GET.get('next', 'core:index')
                return redirect(next_url)
            else:
                messages.error(request, 'Invalid username or password')
    else:
        form = UserLoginForm()
    
    return render(request, 'core/auth/login.html', {'form': form})

def register_view(request):
    """
    View for user registration
    """
    if request.user.is_authenticated:
        return redirect('core:index')
        
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('core:index')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'core/auth/register.html', {'form': form})

# Main application views
@login_required
def index(request):
    """
    View for rendering the homepage
    """
    return render(request, 'core/index.html')

@login_required
def delete_ip_object_form_view(request):
    """
    View for displaying and processing the IP object deletion form
    """
    if request.method == 'POST':
        form = DeleteIPObjectForm(request.POST)
        
        if form.is_valid():
            # Get form data
            firewall_type = form.cleaned_data['firewall_type']
            ip_object_id = form.cleaned_data['ip_object_id']
            auto_commit = form.cleaned_data['auto_commit']
            connection_params = form.get_connection_params()
            
            # Submit the delete task asynchronously
            task = delete_ip_object.delay(
                firewall_type=firewall_type,
                ip_object_id=ip_object_id,
                connection_params=connection_params,
                auto_commit=auto_commit
            )
            
            # Set success message
            messages.success(
                request, 
                f'IP Object deletion task submitted. Task ID: {task.id}'
            )
            
            # Redirect to the task status page
            return redirect(reverse('core:task_status_view', args=[task.id]))
    else:
        form = DeleteIPObjectForm()
    
    return render(request, 'core/delete_ip_form.html', {'form': form})

@login_required
def task_status_view_ui(request, task_id):
    """
    View for displaying the status of a task
    """
    task_result = AsyncResult(task_id)
    
    # Prepare task data for template
    task_data = {
        'task_id': task_id,
        'status': task_result.status,
        'ready': task_result.ready(),
        'successful': task_result.successful() if task_result.ready() else None,
    }
    
    # Add result info if the task has completed
    if task_result.ready():
        if task_result.successful():
            task_data['result'] = task_result.get()
        else:
            task_data['error'] = str(task_result.result)
    
    # Render the template with task data
    return render(request, 'core/task_status.html', {'task': task_data})

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def delete_ip_object_view(request):
    """
    API endpoint to delete an IP object from a firewall
    
    Expects JSON payload with:
    - firewall_type: Type of firewall ('checkpoint', 'fortinet', 'test')
    - ip_object_id: ID of the IP object to delete
    - connection_params: Connection parameters for the firewall
    - auto_commit: (Optional) Whether to automatically commit changes (default: True)
    
    Returns JSON response with task_id for tracking
    """
    try:
        # Parse the request body as JSON
        data = json.loads(request.body)
        
        # Extract required parameters
        firewall_type = data.get('firewall_type')
        ip_object_id = data.get('ip_object_id')
        connection_params = data.get('connection_params', {})
        auto_commit = data.get('auto_commit', True)
        
        # Validate required parameters
        if not firewall_type:
            return JsonResponse({'error': 'firewall_type is required'}, status=400)
        if not ip_object_id:
            return JsonResponse({'error': 'ip_object_id is required'}, status=400)
            
        # Submit the delete task asynchronously
        task = delete_ip_object.delay(
            firewall_type=firewall_type,
            ip_object_id=ip_object_id,
            connection_params=connection_params,
            auto_commit=auto_commit
        )
        
        # Return the task ID for tracking
        return JsonResponse({
            'status': 'task_submitted',
            'task_id': task.id,
            'message': f'Delete task for IP object {ip_object_id} submitted successfully'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON payload'}, status=400)
    except Exception as e:
        logger.exception(f"Error processing delete request: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["GET"])
@login_required
def task_status_view(request, task_id):
    """
    API endpoint to check the status of a task
    
    Args:
        task_id: The ID of the task to check
        
    Returns:
        JSON response with task status
    """
    from celery.result import AsyncResult
    
    task_result = AsyncResult(task_id)
    
    result = {
        'task_id': task_id,
        'status': task_result.status,
    }
    
    # Add result info if the task has completed
    if task_result.ready():
        if task_result.successful():
            result['result'] = task_result.get()
        else:
            result['error'] = str(task_result.result)
    
    return JsonResponse(result)