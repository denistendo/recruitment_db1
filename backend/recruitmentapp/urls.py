from django.urls import path
from . import views

app_name = 'recruitmentapp'

urlpatterns = [
    path('', views.users_page, name='users'),
    path('jobs/', views.jobs_page, name='jobs'),

    path('api/users/', views.api_user_list, name='api_user_list'),
    path('api/users/create/', views.api_user_create, name='api_user_create'),
    path('api/users/update/<int:user_id>/', views.api_user_update, name='api_user_update'),
    path('api/users/delete/<int:user_id>/', views.api_user_delete, name='api_user_delete'),

    path('api/jobs/', views.api_job_list, name='api_job_list'),
    path('api/jobs/create/', views.api_job_create, name='api_job_create'),
    path('api/jobs/update/<int:job_id>/', views.api_job_update, name='api_job_update'),
    path('api/jobs/delete/<int:job_id>/', views.api_job_delete, name='api_job_delete'),
]

