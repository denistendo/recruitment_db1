from django.urls import path
from . import views

# ==============================================================================
# Django Local URL Routing
# Purpose:
#   Maps incoming web requests (based on the path in the browser URL bar or
#   AJAX request) to the specific Python function in views.py that handles it.
# ==============================================================================

app_name = 'recruitmentapp'

urlpatterns = [
    # 1. Main Dashboard View
    # Maps http://127.0.0.1:8000/ to views.dashboard_index
    path('', views.dashboard_index, name='dashboard'),

    # 2. JSON Endpoint: List all Jobs
    # Maps GET requests on /api/jobs/ to views.api_job_list
    path('api/jobs/', views.api_job_list, name='api_job_list'),

    # 3. JSON Endpoint: Create a Job
    # Maps POST requests on /api/jobs/create/ to views.api_job_create
    path('api/jobs/create/', views.api_job_create, name='api_job_create'),

    # 4. JSON Endpoint: Delete a Job
    # Maps DELETE requests on /api/jobs/delete/<id>/ to views.api_job_delete
    # The <int:job_id> part ensures that Django captures the integer ID from the
    # URL and passes it as a parameter 'job_id' to the view function.
    path('api/jobs/delete/<int:job_id>/', views.api_job_delete, name='api_job_delete'),
]
