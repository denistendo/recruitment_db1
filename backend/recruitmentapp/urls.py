from django.urls import path
from . import views

app_name = 'recruitmentapp'

urlpatterns = [
    # Auth
    path('signup/', views.signup_view, name='signup'),
    path('signin/', views.signin_view, name='signin'),
    path('logout/', views.logout_view, name='logout'),

    # Dashboards
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('hr-dashboard/', views.hr_dashboard, name='hr_dashboard'),
    path('panel-dashboard/', views.panel_dashboard, name='panel_dashboard'),
    path('applicant-dashboard/', views.applicant_dashboard, name='applicant_dashboard'),
    path('department-dashboard/', views.department_dashboard, name='department_dashboard'),

    # Panel Member
    path('my-interviews/', views.my_interviews, name='my_interviews'),
    path('candidate-profile/<int:applicant_id>/', views.candidate_profile, name='candidate_profile'),
    path('conduct-interview/<int:application_id>/', views.conduct_interview, name='conduct_interview'),

    # Functional pages
    path('users/', views.users_page, name='users'),
    path('jobs/', views.jobs_page, name='jobs'),
    path('applicants/', views.applicants_page, name='applicants'),
    path('applications/', views.applications_page, name='applications'),
    path('profile/', views.applicant_profile, name='applicant_profile'),

    # HR Applications Management
    path('hr-applications/', views.hr_applications_view, name='hr_applications'),
    path('applicant/<int:applicant_id>/', views.applicant_detail, name='applicant_detail'),
    path('application/shortlist/<int:application_id>/', views.application_shortlist, name='application_shortlist'),
    path('application/reject/<int:application_id>/', views.application_reject, name='application_reject'),
    path('application/schedule/<int:application_id>/', views.schedule_interview, name='schedule_interview'),

    # HR Department Management
    path('departments/', views.departments_view, name='departments'),
    path('departments/add/', views.department_add, name='department_add'),
    path('departments/edit/<int:department_id>/', views.department_edit, name='department_edit'),
    path('departments/delete/<int:department_id>/', views.department_delete, name='department_delete'),
    path('departments/<int:department_id>/jobs/', views.department_jobs, name='department_jobs'),

    # API endpoints
    path('api/signup/', views.api_signup, name='api_signup'),
    path('api/users/', views.api_user_list, name='api_user_list'),
    path('api/users/create/', views.api_user_create, name='api_user_create'),
    path('api/users/update/<int:user_id>/', views.api_user_update, name='api_user_update'),
    path('api/users/delete/<int:user_id>/', views.api_user_delete, name='api_user_delete'),
    path('api/jobs/', views.api_job_list, name='api_job_list'),
    path('api/jobs/create/', views.api_job_create, name='api_job_create'),
    path('api/jobs/update/<int:job_id>/', views.api_job_update, name='api_job_update'),
    path('api/jobs/delete/<int:job_id>/', views.api_job_delete, name='api_job_delete'),
    path('api/applicants/', views.api_applicant_list, name='api_applicant_list'),
    path('api/applicants/create/', views.api_applicant_create, name='api_applicant_create'),
    path('api/applicants/update/<int:applicant_id>/', views.api_applicant_update, name='api_applicant_update'),
    path('api/applicants/delete/<int:applicant_id>/', views.api_applicant_delete, name='api_applicant_delete'),
    path('api/jobs/open/', views.api_open_jobs, name='api_open_jobs'),
    path('api/applications/apply/', views.api_apply_job, name='api_apply_job'),
    path('api/applications/', views.api_application_list, name='api_application_list'),
    path('api/applications/create/', views.api_application_create, name='api_application_create'),
    path('api/applications/update/<int:application_id>/', views.api_application_update, name='api_application_update'),
    path('api/applications/delete/<int:application_id>/', views.api_application_delete, name='api_application_delete'),
    path('api/qualifications/save/', views.api_save_qualifications, name='api_save_qualifications'),
    path('api/qualifications/create/', views.api_qualification_create, name='api_qualification_create'),
    path('api/qualifications/update/<int:qualification_id>/', views.api_qualification_update, name='api_qualification_update'),
    path('api/qualifications/delete/<int:qualification_id>/', views.api_qualification_delete, name='api_qualification_delete'),
    path('api/skills/save/', views.api_save_skills, name='api_save_skills'),
    path('api/applicant-skills/create/', views.api_applicant_skill_create, name='api_applicant_skill_create'),
    path('api/applicant-skills/update/<int:applicant_skill_id>/', views.api_applicant_skill_update, name='api_applicant_skill_update'),
    path('api/applicant-skills/delete/<int:applicant_skill_id>/', views.api_applicant_skill_delete, name='api_applicant_skill_delete'),
    path('api/profile/update/', views.api_update_profile, name='api_update_profile'),
]
