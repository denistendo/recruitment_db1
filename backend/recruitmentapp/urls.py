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
    path('', views.dashboard_index, name='dashboard'),

    # 2. JSON Endpoints: Users CRUD
    path('api/users/', views.api_user_list, name='api_user_list'),
    path('api/users/create/', views.api_user_create, name='api_user_create'),
    path('api/users/update/<int:user_id>/', views.api_user_update, name='api_user_update'),
    path('api/users/delete/<int:user_id>/', views.api_user_delete, name='api_user_delete'),

    # 3. JSON Endpoints: Jobs CRUD
    path('api/jobs/', views.api_job_list, name='api_job_list'),
    path('api/jobs/create/', views.api_job_create, name='api_job_create'),
    path('api/jobs/update/<int:job_id>/', views.api_job_update, name='api_job_update'),
    path('api/jobs/delete/<int:job_id>/', views.api_job_delete, name='api_job_delete'),
]
