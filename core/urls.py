from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Web UI routes
    path('', views.index, name='index'),
    path('firewall/ip-objects/delete/', views.delete_ip_object_form_view, name='delete_ip_form'),
    path('tasks/<str:task_id>/', views.task_status_view_ui, name='task_status_view'),
    
    # API routes
    path('api/firewall/ip-objects/delete/', views.delete_ip_object_view, name='delete_ip_object'),
    path('api/tasks/<str:task_id>/', views.task_status_view, name='task_status'),
]