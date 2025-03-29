from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class UserLoginForm(forms.Form):
    """
    Form for user login
    """
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'})
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
    )

class UserRegistrationForm(UserCreationForm):
    """
    Form for user registration
    """
    email = forms.EmailField(
        max_length=254,
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'})
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super(UserRegistrationForm, self).__init__(*args, **kwargs)
        
        # Add bootstrap classes to form fields
        for field_name in self.fields:
            self.fields[field_name].widget.attrs['class'] = 'form-control'
            if field_name == 'username':
                self.fields[field_name].widget.attrs['placeholder'] = 'Username'
            elif field_name == 'password1':
                self.fields[field_name].widget.attrs['placeholder'] = 'Password'
            elif field_name == 'password2':
                self.fields[field_name].widget.attrs['placeholder'] = 'Confirm Password'

class DeleteIPObjectForm(forms.Form):
    """
    Form for deleting an IP object from a firewall
    """
    FIREWALL_CHOICES = [
        ('test', 'Test Firewall (Development)'),
        ('checkpoint', 'Check Point Firewall'),
        ('fortinet', 'Fortinet FortiGate Firewall'),
    ]
    
    firewall_type = forms.ChoiceField(
        choices=FIREWALL_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text="Select the type of firewall"
    )
    
    ip_object_id = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text="Name or ID of the IP object to delete"
    )
    
    # Connection parameters
    host = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text="Hostname or IP address of the firewall",
        required=False
    )
    
    username = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text="Username for authentication",
        required=False
    )
    
    password = forms.CharField(
        max_length=255,
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text="Password for authentication",
        required=False
    )
    
    port = forms.IntegerField(
        min_value=1,
        max_value=65535,
        initial=443,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text="API port (default: 443)",
        required=False
    )
    
    domain = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text="Domain name (for Check Point)",
        required=False
    )
    
    vdom = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text="Virtual domain (for FortiGate)",
        required=False
    )
    
    auto_commit = forms.BooleanField(
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Automatically commit changes after deletion"
    )
    
    def clean(self):
        cleaned_data = super().clean()
        firewall_type = cleaned_data.get('firewall_type')
        
        # Skip validation for test firewall
        if firewall_type == 'test':
            return cleaned_data
            
        # Validate required fields for different firewall types
        if firewall_type in ['checkpoint', 'fortinet']:
            required_fields = ['host']
            if firewall_type == 'checkpoint':
                required_fields.extend(['username', 'password'])
            
            for field in required_fields:
                if not cleaned_data.get(field):
                    self.add_error(field, f"This field is required for {firewall_type} firewalls")
        
        return cleaned_data
    
    def get_connection_params(self):
        """
        Get connection parameters as a dictionary
        """
        params = {}
        for field in ['host', 'username', 'password', 'port', 'domain', 'vdom']:
            value = self.cleaned_data.get(field)
            if value:
                params[field] = value
                
        return params