from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.db.models import Q, Count
from functools import wraps
from datetime import date
from .mailer import send_application_confirmation, send_interview_scheduled, send_accepted, send_interviewed, send_rejected
import json
from .models import JobPostings, Departments, Users, Applicants, Applications, Qualifications, ApplicantSkills, Skills, Interviews, InterviewPanel, JobPanelAssignment


def _create_interview_panel_if_needed(full_name):
    if full_name and not InterviewPanel.objects.filter(full_name=full_name).exists():
        max_id = InterviewPanel.objects.order_by('-panel_id').first()
        next_id = (max_id.panel_id + 1) if max_id else 1
        InterviewPanel.objects.create(
            panel_id=next_id,
            full_name=full_name,
            role='Interview Panel Member'
        )


ROLE_DASHBOARD_MAP = {
    'SystemAdministrator': 'recruitmentapp:admin_dashboard',
    'HumanResourceOfficer': 'recruitmentapp:hr_dashboard',
    'InterviewPanelMember': 'recruitmentapp:panel_dashboard',
    'JobApplicant': 'recruitmentapp:applicant_dashboard',
    'DepartmentManager': 'recruitmentapp:department_dashboard',
}


def login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if 'user_id' not in request.session:
            messages.error(request, 'Please log in to continue.')
            return redirect('recruitmentapp:signin')
        return view_func(request, *args, **kwargs)
    return wrapper


def role_required(allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if 'user_id' not in request.session:
                messages.error(request, 'Please log in to continue.')
                return redirect('recruitmentapp:signin')
            user_type = request.session.get('user_type')
            if user_type not in allowed_roles:
                messages.error(request, 'You do not have permission to access this page.')
                dashboard_url = ROLE_DASHBOARD_MAP.get(user_type, 'recruitmentapp:signin')
                return redirect(dashboard_url)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


# ========== AUTHENTICATION VIEWS ==========

def signup_view(request):
    form_data = {}
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')[:15]
        confirm_password = request.POST.get('confirm_password', '')[:15]
        user_type = request.POST.get('user_type', '').strip()

        form_data = {
            'full_name': full_name,
            'email': email,
            'password': password,
            'confirm_password': confirm_password,
            'user_type': user_type,
        }

        if not all([full_name, email, password, confirm_password, user_type]):
            messages.error(request, 'All fields are required.')
            return render(request, 'authentication/signup.html', {'form_data': form_data})

        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'authentication/signup.html', {'form_data': form_data})

        if Users.objects.filter(email=email).exists():
            messages.error(request, 'A user with this email already exists.')
            return render(request, 'authentication/signup.html', {'form_data': form_data})

        max_id = Users.objects.order_by('-user_id').first()
        next_id = (max_id.user_id + 1) if max_id else 1

        user = Users.objects.create(
            user_id=next_id,
            full_name=full_name,
            email=email,
            password=password,
            user_type=user_type
        )

        if user_type == 'InterviewPanelMember':
            _create_interview_panel_if_needed(full_name)

        messages.success(request, 'Account created successfully! Please log in.')
        return redirect('recruitmentapp:signin')

    return render(request, 'authentication/signup.html')


def signin_view(request):
    form_data = {}
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')[:15]

        form_data = {
            'email': email,
            'password': password,
        }

        if not all([email, password]):
            messages.error(request, 'All fields are required.')
            return render(request, 'authentication/signin.html', {'form_data': form_data})

        user = Users.objects.filter(email=email).first()
        if not user or user.password != password:
            messages.error(request, 'Invalid credentials.')
            return render(request, 'authentication/signin.html', {'form_data': form_data})

        request.session['user_id'] = user.user_id
        request.session['user_type'] = user.user_type
        request.session.set_expiry(86400)

        redirect_url = ROLE_DASHBOARD_MAP.get(user.user_type, 'recruitmentapp:users')
        return redirect(redirect_url)

    return render(request, 'authentication/signin.html')


def logout_view(request):
    request.session.flush()
    messages.success(request, 'You have been logged out.')
    return redirect('recruitmentapp:signin')


# ========== DASHBOARD VIEWS ==========

@role_required(['SystemAdministrator'])
def admin_dashboard(request):
    context = {
        'active_tab': 'dashboard',
        'total_users': Users.objects.count(),
        'total_jobs': JobPostings.objects.count(),
        'total_applications': Applications.objects.count(),
        'recent_users': Users.objects.all().order_by('-user_id')[:5],
    }
    return render(request, 'dashboards/admin_dashboard.html', context)


@role_required(['HumanResourceOfficer'])
def hr_dashboard(request):
    context = {
        'active_tab': 'dashboard',
        'total_jobs': JobPostings.objects.count(),
        'total_applications': Applications.objects.count(),
        'recent_jobs': JobPostings.objects.select_related('department').all().order_by('-job_id')[:5],
    }
    return render(request, 'dashboards/hr_dashboard.html', context)


@role_required(['InterviewPanelMember'])
def panel_dashboard(request):
    user_id = request.session.get('user_id')
    user = Users.objects.get(pk=user_id)

    panel_member = InterviewPanel.objects.filter(full_name=user.full_name).first()
    if not panel_member and user.user_type == 'InterviewPanelMember':
        _create_interview_panel_if_needed(user.full_name)
        panel_member = InterviewPanel.objects.filter(full_name=user.full_name).first()

    total_interviews = 0
    pending_interviews = 0
    completed_interviews = 0

    if panel_member:
        interviewer_prefix = f'Interviewer: {panel_member.full_name}'
        assigned_interviews = Interviews.objects.filter(remarks__startswith=interviewer_prefix)
        total_interviews = assigned_interviews.count()
        completed_interviews = assigned_interviews.filter(score__isnull=False).count()
        pending_interviews = total_interviews - completed_interviews

    context = {
        'active_tab': 'dashboard',
        'panel_member': panel_member,
        'total_interviews': total_interviews,
        'pending_interviews': pending_interviews,
        'completed_interviews': completed_interviews,
    }
    return render(request, 'dashboards/panel_dashboard.html', context)


@role_required(['InterviewPanelMember'])
def my_interviews(request):
    user_id = request.session.get('user_id')
    user = Users.objects.get(pk=user_id)
    panel_member = InterviewPanel.objects.filter(full_name=user.full_name).first()
    if not panel_member and user.user_type == 'InterviewPanelMember':
        _create_interview_panel_if_needed(user.full_name)
        panel_member = InterviewPanel.objects.filter(full_name=user.full_name).first()

    interviews_list = []
    if panel_member:
        interviewer_prefix = f'Interviewer: {panel_member.full_name}'
        assigned_interviews = Interviews.objects.filter(remarks__startswith=interviewer_prefix).select_related('application__applicant__user', 'application__job')
        for interview in assigned_interviews:
            app = interview.application
            assigned_interviewer = ''
            if interview.remarks and 'Interviewer:' in interview.remarks:
                assigned_interviewer = interview.remarks.split('\n')[0].replace('Interviewer: ', '')
            interviews_list.append({
                'application': app,
                'interview': interview,
                'interview_date': interview.interview_date if interview else None,
                'interview_mode': interview.interview_mode if interview else None,
                'assigned_interviewer': assigned_interviewer,
            })

    context = {
        'active_tab': 'my_interviews',
        'interviews_list': interviews_list,
        'panel_member': panel_member,
    }
    return render(request, 'dashboards/my_interviews.html', context)


@role_required(['InterviewPanelMember'])
def candidate_profile(request, applicant_id):
    try:
        applicant = Applicants.objects.select_related('user').get(pk=applicant_id)
    except Applicants.DoesNotExist:
        messages.error(request, 'Applicant not found.')
        return redirect('recruitmentapp:my_interviews')

    qualifications = Qualifications.objects.filter(applicant=applicant).order_by('-year_completed')
    skills_list = ApplicantSkills.objects.filter(applicant=applicant).select_related('skill')

    context = {
        'active_tab': 'my_interviews',
        'applicant': applicant,
        'user': applicant.user,
        'qualifications': qualifications,
        'skills_list': skills_list,
    }
    return render(request, 'dashboards/candidate_profile.html', context)


@role_required(['InterviewPanelMember'])
def conduct_interview(request, application_id):
    try:
        app = Applications.objects.select_related('applicant__user', 'job').get(pk=application_id)
    except Applications.DoesNotExist:
        messages.error(request, 'Application not found.')
        return redirect('recruitmentapp:my_interviews')

    interview = Interviews.objects.filter(application=app).first()

    if request.method == 'POST':
        action = request.POST.get('action', 'submit')

        if action == 'no_show':
            if app.status == 'Interview Scheduled':
                app.status = 'Not Interviewed'
                app.save()
            messages.success(request, f'{app.applicant.user.full_name} marked as not interviewed.')
            return redirect('recruitmentapp:my_interviews')

        score = request.POST.get('score')
        remarks = request.POST.get('remarks', '').strip()

        if not score:
            messages.error(request, 'Score is required.')
            return render(request, 'dashboards/conduct_interview.html', {
                'active_tab': 'my_interviews',
                'application': app,
                'interview': interview,
                'applicant': app.applicant,
            })

        try:
            score = int(score)
        except (ValueError, TypeError):
            messages.error(request, 'Score must be a number.')
            return render(request, 'dashboards/conduct_interview.html', {
                'active_tab': 'my_interviews',
                'application': app,
                'interview': interview,
                'applicant': app.applicant,
            })

        if interview:
            interview.score = score
            if remarks:
                prefix = ''
                if interview.remarks and 'Interviewer:' in interview.remarks:
                    prefix = interview.remarks.split('\n')[0] + '\n'
                interview.remarks = prefix + remarks
            else:
                interview.remarks = interview.remarks or None
            interview.save()
            if app.status == 'Interview Scheduled':
                app.status = 'Interviewed'
                app.save()
            messages.success(request, 'Interview results updated successfully!')
        else:
            max_id = Interviews.objects.order_by('-interview_id').first()
            next_id = (max_id.interview_id + 1) if max_id else 1
            Interviews.objects.create(
                interview_id=next_id,
                application=app,
                interview_date=app.application_date,
                interview_mode='In-Person',
                score=score,
                remarks=remarks or None,
            )
            if app.status == 'Interview Scheduled':
                app.status = 'Interviewed'
                app.save()
            messages.success(request, 'Interview results submitted successfully!')

        if app.status == 'Interviewed':
            try:
                send_interviewed(app.applicant.user.email, app.applicant.user.full_name, app.job.title)
            except Exception:
                pass

        return redirect('recruitmentapp:my_interviews')

    panel_remarks = ''
    if interview and interview.remarks:
        if 'Interviewer:' in interview.remarks and '\n' in interview.remarks:
            panel_remarks = interview.remarks.split('\n', 1)[1]
        elif 'Interviewer:' not in interview.remarks:
            panel_remarks = interview.remarks

    context = {
        'active_tab': 'my_interviews',
        'application': app,
        'interview': interview,
        'applicant': app.applicant,
        'panel_remarks': panel_remarks,
    }
    return render(request, 'dashboards/conduct_interview.html', context)


@role_required(['JobApplicant'])
def applicant_dashboard(request):
    user_id = request.session.get('user_id')
    applicant = Applicants.objects.filter(user_id=user_id).first()
    applications = []
    applied_job_ids = []
    if applicant:
        applications = Applications.objects.filter(applicant=applicant).select_related('job').all()
        applied_job_ids = [app.job_id for app in applications if app.job_id]
    open_jobs = JobPostings.objects.select_related('department').all()
    if applied_job_ids:
        open_jobs = open_jobs.exclude(job_id__in=applied_job_ids)
    context = {
        'active_tab': 'dashboard',
        'applicant': applicant,
        'applications': applications,
        'total_applications': len(applications),
        'total_open_positions': open_jobs.count(),
        'open_jobs': open_jobs,
        'applied_job_ids': applied_job_ids,
    }
    return render(request, 'dashboards/applicant_dashboard.html', context)


@role_required(['JobApplicant'])
def applicant_profile(request):
    user_id = request.session.get('user_id')
    applicant = Applicants.objects.filter(user_id=user_id).first()
    user = Users.objects.get(pk=user_id)

    if request.method == 'POST':
        date_of_birth = request.POST.get('date_of_birth')
        gender = request.POST.get('gender')
        phone_number = request.POST.get('phone_number')
        address = request.POST.get('address')

        if applicant:
            applicant.date_of_birth = date_of_birth if date_of_birth else None
            applicant.gender = gender or None
            applicant.phone_number = phone_number or None
            applicant.address = address or None
            applicant.save()
            messages.success(request, 'Profile updated successfully!')
        else:
            max_id = Applicants.objects.order_by('-applicant_id').first()
            next_id = (max_id.applicant_id + 1) if max_id else 1
            applicant = Applicants.objects.create(
                applicant_id=next_id,
                user_id=user_id,
                date_of_birth=date_of_birth if date_of_birth else None,
                gender=gender or None,
                phone_number=phone_number or None,
                address=address or None
            )
            messages.success(request, 'Profile created successfully!')

        return redirect('recruitmentapp:applicant_profile')

    qualifications = Qualifications.objects.filter(applicant=applicant).order_by('-year_completed') if applicant else []
    skills_list = ApplicantSkills.objects.filter(applicant=applicant).select_related('skill') if applicant else []
    all_skills = Skills.objects.all().order_by('skill_name')

    total_applications = 0
    total_interviews = 0
    latest_application = None
    if applicant:
        apps = Applications.objects.filter(applicant=applicant)
        total_applications = apps.count()
        latest_application = apps.order_by('-application_id').first()
        total_interviews = Interviews.objects.filter(application__applicant=applicant).count()

    completion = 0
    if applicant:
        completion += 25
        if applicant.date_of_birth:
            completion += 25
    if qualifications:
        completion += 25
    if skills_list:
        completion += 25

    context = {
        'active_tab': 'profile',
        'applicant': applicant,
        'user': user,
        'qualifications': qualifications,
        'skills_list': skills_list,
        'all_skills': all_skills,
        'total_applications': total_applications,
        'total_interviews': total_interviews,
        'latest_application': latest_application,
        'completion': completion,
    }
    return render(request, 'profile/profile.html', context)


# ========== APPLICANT APIS ==========

@role_required(['JobApplicant'])
def api_open_jobs(request):
    jobs = JobPostings.objects.select_related('department').all().order_by('-job_id')
    data = []
    for job in jobs:
        data.append({
            'job_id': job.job_id,
            'title': job.title,
            'description': job.description,
            'department_name': job.department.department_name if job.department else 'N/A',
            'posted_date': str(job.posted_date) if job.posted_date else '',
            'closing_date': str(job.closing_date) if job.closing_date else '',
        })
    return JsonResponse({'status': 'success', 'jobs': data})


@csrf_exempt
@role_required(['JobApplicant'])
@require_http_methods(["POST"])
def api_apply_job(request):
    try:
        data = json.loads(request.body)
        job_id = data.get('job_id')
        user_id = request.session.get('user_id')

        applicant = Applicants.objects.filter(user_id=user_id).first()
        if not applicant:
            return JsonResponse({'status': 'error', 'message': 'Please complete your profile before applying.'}, status=400)

        try:
            job = JobPostings.objects.get(pk=job_id)
        except JobPostings.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Job not found.'}, status=404)

        if Applications.objects.filter(applicant=applicant, job=job).exists():
            return JsonResponse({'status': 'error', 'message': 'You have already applied for this job.'}, status=400)

        max_id = Applications.objects.order_by('-application_id').first()
        next_id = (max_id.application_id + 1) if max_id else 1

        Applications.objects.create(
            application_id=next_id,
            applicant=applicant,
            job=job,
            application_date=date.today(),
            status='Pending'
        )

        try:
            user = Users.objects.get(pk=user_id)
            send_application_confirmation(user.email, user.full_name, job.title, applicant.phone_number if applicant else None)
        except Exception:
            pass

        return JsonResponse({'status': 'success', 'message': 'Application submitted successfully!'}, status=201)

    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON data.'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
@role_required(['JobApplicant'])
@require_http_methods(["POST"])
def api_save_qualifications(request):
    try:
        data = json.loads(request.body)
        user_id = request.session.get('user_id')
        applicant = Applicants.objects.filter(user_id=user_id).first()
        if not applicant:
            return JsonResponse({'status': 'error', 'message': 'Applicant profile not found.'}, status=400)

        Qualifications.objects.filter(applicant=applicant).delete()

        items = data.get('qualifications', [])
        for item in items:
            max_id = Qualifications.objects.order_by('-qualification_id').first()
            next_id = (max_id.qualification_id + 1) if max_id else 1
            Qualifications.objects.create(
                qualification_id=next_id,
                applicant=applicant,
                institution=item.get('institution'),
                award=item.get('award'),
                year_completed=item.get('year_completed')
            )

        return JsonResponse({'status': 'success', 'message': 'Qualifications saved successfully!'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
@role_required(['JobApplicant'])
@require_http_methods(["POST"])
def api_save_skills(request):
    try:
        data = json.loads(request.body)
        user_id = request.session.get('user_id')
        applicant = Applicants.objects.filter(user_id=user_id).first()
        if not applicant:
            return JsonResponse({'status': 'error', 'message': 'Applicant profile not found.'}, status=400)

        ApplicantSkills.objects.filter(applicant=applicant).delete()

        items = data.get('skills', [])
        for skill_id in items:
            try:
                skill = Skills.objects.get(pk=skill_id)
            except Skills.DoesNotExist:
                continue
            max_id = ApplicantSkills.objects.order_by('-applicant_skill_id').first()
            next_id = (max_id.applicant_skill_id + 1) if max_id else 1
            ApplicantSkills.objects.create(
                applicant_skill_id=next_id,
                applicant=applicant,
                skill=skill,
                proficiency_level='Intermediate'
            )

        return JsonResponse({'status': 'success', 'message': 'Skills saved successfully!'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@role_required(['DepartmentManager'])
def department_dashboard(request):
    context = {
        'active_tab': 'dashboard',
    }
    return render(request, 'dashboards/department_dashboard.html', context)


# ========== FUNCTIONAL PAGES ==========

@role_required(['SystemAdministrator'])
def users_page(request):
    users = Users.objects.all().order_by('user_id')
    context = {
        'users': users,
        'active_tab': 'users',
    }
    return render(request, 'users/users.html', context)


@role_required(['SystemAdministrator', 'HumanResourceOfficer'])
def jobs_page(request):
    jobs = JobPostings.objects.select_related('department').all().order_by('job_id')
    departments = Departments.objects.all().order_by('department_name')
    context = {
        'jobs': jobs,
        'departments': departments,
        'active_tab': 'jobs',
    }
    return render(request, 'jobs/jobs.html', context)


@role_required(['SystemAdministrator', 'HumanResourceOfficer'])
def applicants_page(request):
    applicants_list = Applicants.objects.select_related('user').all().order_by('applicant_id')
    users = Users.objects.all().order_by('full_name')
    context = {
        'applicants': applicants_list,
        'users': users,
        'active_tab': 'applicants',
    }
    return render(request, 'applicants/applicants.html', context)


@role_required(['SystemAdministrator', 'HumanResourceOfficer', 'JobApplicant'])
def applications_page(request):
    user_id = request.session.get('user_id')
    user_type = request.session.get('user_type')

    if user_type == 'JobApplicant':
        applicant = Applicants.objects.filter(user_id=user_id).first()
        if applicant:
            applications_list = Applications.objects.filter(applicant=applicant).select_related('applicant__user', 'job').all()
        else:
            applications_list = []
    else:
        applications_list = Applications.objects.select_related('applicant__user', 'job').all().order_by('-application_id')

    applicants_list = Applicants.objects.select_related('user').all().order_by('applicant_id')
    jobs_list = JobPostings.objects.select_related('department').all().order_by('title')

    context = {
        'applications': applications_list,
        'applicants_list': applicants_list,
        'jobs_list': jobs_list,
        'active_tab': 'applications',
    }
    return render(request, 'applications/applications.html', context)


# ========== HR APPLICANT DETAIL VIEW ==========

@role_required(['SystemAdministrator', 'HumanResourceOfficer'])
def applicant_detail(request, applicant_id):
    try:
        applicant = Applicants.objects.select_related('user').get(pk=applicant_id)
    except Applicants.DoesNotExist:
        messages.error(request, 'Applicant not found.')
        return redirect('recruitmentapp:applicants')

    qualifications = Qualifications.objects.filter(applicant=applicant).order_by('-year_completed')
    skills_list = ApplicantSkills.objects.filter(applicant=applicant).select_related('skill')
    applications = Applications.objects.filter(applicant=applicant).select_related('job').order_by('-application_id')

    context = {
        'active_tab': 'hr_applications',
        'applicant': applicant,
        'user': applicant.user,
        'qualifications': qualifications,
        'skills_list': skills_list,
        'applications': applications,
    }
    return render(request, 'applications/applicant_detail.html', context)


# ========== HR APPLICATIONS MANAGEMENT ==========

@role_required(['HumanResourceOfficer'])
def hr_applications_view(request):
    search = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', '').strip()

    applications_list = Applications.objects.select_related('applicant__user', 'job').all().order_by('-application_id')

    if search:
        applications_list = applications_list.filter(
            Q(applicant__user__full_name__icontains=search) |
            Q(job__title__icontains=search)
        )

    if status_filter:
        applications_list = applications_list.filter(status__iexact=status_filter)

    interview_ids = [a.application_id for a in applications_list]
    interviews_qs = Interviews.objects.filter(application_id__in=interview_ids)
    interview_map = {iv.application_id: iv for iv in interviews_qs}

    enriched_apps = []
    for app in applications_list:
        app.interview_obj = interview_map.get(app.application_id)
        enriched_apps.append(app)

    status_counts = {}
    for app in enriched_apps:
        s = app.status or 'Pending'
        status_counts[s] = status_counts.get(s, 0) + 1

    context = {
        'applications': enriched_apps,
        'status_counts': status_counts,
        'current_search': search,
        'current_status': status_filter,
        'active_tab': 'hr_applications',
    }
    return render(request, 'applications/hr_applications.html', context)


@role_required(['HumanResourceOfficer'])
def application_reject(request, application_id):
    try:
        app = Applications.objects.select_related('applicant__user', 'job').get(pk=application_id)
        app.status = 'Rejected'
        app.save()
        try:
            send_rejected(app.applicant.user.email, app.applicant.user.full_name, app.job.title)
        except Exception:
            pass
        messages.success(request, f'Application #{application_id} has been rejected.')
    except Applications.DoesNotExist:
        messages.error(request, 'Application not found.')
    return redirect('recruitmentapp:hr_applications')


@role_required(['HumanResourceOfficer'])
def application_accept(request, application_id):
    try:
        app = Applications.objects.select_related('applicant__user', 'job').get(pk=application_id)
        app.status = 'Accepted'
        app.save()
        try:
            send_accepted(app.applicant.user.email, app.applicant.user.full_name, app.job.title)
        except Exception:
            pass
        messages.success(request, f'Application #{application_id} has been accepted.')
    except Applications.DoesNotExist:
        messages.error(request, 'Application not found.')
    return redirect('recruitmentapp:hr_applications')


@role_required(['HumanResourceOfficer'])
def schedule_interview(request, application_id):
    try:
        app = Applications.objects.select_related('applicant__user', 'job__department').get(pk=application_id)
    except Applications.DoesNotExist:
        messages.error(request, 'Application not found.')
        return redirect('recruitmentapp:hr_applications')

    registered_names = Users.objects.filter(user_type='InterviewPanelMember').values_list('full_name', flat=True)
    panel_members = InterviewPanel.objects.filter(
        full_name__in=registered_names
    ).filter(
        Q(department=app.job.department) | Q(department__isnull=True)
    ).order_by('full_name') if app.job.department else InterviewPanel.objects.filter(
        full_name__in=registered_names
    ).order_by('full_name')

    interview = Interviews.objects.filter(application=app).first()

    if request.method == 'POST':
        interviewer_id = request.POST.get('interviewer')
        interview_date = request.POST.get('interview_date')
        interview_time = request.POST.get('interview_time')
        interview_mode = request.POST.get('interview_mode', 'In-Person')

        if not interview_date:
            messages.error(request, 'Interview date is required.')
            return render(request, 'applications/schedule_interview.html', {
                'active_tab': 'hr_applications',
                'application': app,
                'interview': interview,
                'panel_members': panel_members,
            })

        selected_interviewer = None
        if interviewer_id:
            try:
                selected_interviewer = InterviewPanel.objects.get(pk=interviewer_id)
            except InterviewPanel.DoesNotExist:
                pass

        interviewer_prefix = ''
        if selected_interviewer:
            interviewer_prefix = f'Interviewer: {selected_interviewer.full_name}'

        if interview:
            existing_remarks = interview.remarks or ''
            panel_notes = ''
            if existing_remarks and 'Interviewer:' not in existing_remarks:
                panel_notes = existing_remarks
            elif existing_remarks and '\n' in existing_remarks:
                panel_notes = existing_remarks.split('\n', 1)[1]

            interview.interview_date = interview_date
            interview.interview_time = interview_time
            interview.interview_mode = interview_mode
            interview.remarks = interviewer_prefix + ('\n' + panel_notes if panel_notes else '')
            interview.save()
        else:
            max_id = Interviews.objects.order_by('-interview_id').first()
            next_id = (max_id.interview_id + 1) if max_id else 1
            Interviews.objects.create(
                interview_id=next_id,
                application=app,
                interview_date=interview_date,
                interview_time=interview_time,
                interview_mode=interview_mode,
                remarks=interviewer_prefix or None,
            )

        app.status = 'Interview Scheduled'
        app.save()

        try:
            send_interview_scheduled(
                app.applicant.user.email,
                app.applicant.user.full_name,
                app.job.title,
                interview_date,
                interview_time,
                interview_mode,
            )
        except Exception:
            pass

        messages.success(request, f'Interview scheduled for {app.applicant.user.full_name}.')
        return redirect('recruitmentapp:hr_applications')

    context = {
        'active_tab': 'hr_applications',
        'application': app,
        'interview': interview,
        'panel_members': panel_members,
    }
    return render(request, 'applications/schedule_interview.html', context)


# ========== API ENDPOINTS (unchanged) ==========

@csrf_exempt
@require_http_methods(["POST"])
def api_signup(request):
    try:
        data = json.loads(request.body)
        full_name = data.get('full_name', '').strip()
        email = data.get('email', '').strip()
        password = (data.get('password', '') or '')[:15]
        user_type = data.get('user_type', '').strip()

        if not full_name or not email or not password or not user_type:
            return JsonResponse({'status': 'error', 'message': 'All fields are required.'}, status=400)

        if Users.objects.filter(email=email).exists():
            return JsonResponse({'status': 'error', 'message': 'A user with this email already exists.'}, status=400)

        max_id = Users.objects.order_by('-user_id').first()
        next_id = (max_id.user_id + 1) if max_id else 1

        user = Users.objects.create(
            user_id=next_id,
            full_name=full_name,
            email=email,
            password=password,
            user_type=user_type
        )

        if user_type == 'InterviewPanelMember':
            _create_interview_panel_if_needed(full_name)

        return JsonResponse({'status': 'success', 'message': 'Account created successfully!'}, status=201)
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON data.'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


def api_user_list(request):
    users = Users.objects.all().order_by('user_id')
    data = []
    for u in users:
        data.append({
            'user_id': u.user_id,
            'full_name': u.full_name,
            'email': u.email,
            'user_type': u.user_type
        })
    return JsonResponse({'status': 'success', 'users': data})


@csrf_exempt
@require_http_methods(["POST"])
def api_user_create(request):
    try:
        data = json.loads(request.body)
        full_name = data.get('full_name')
        email = data.get('email')
        password = (data.get('password') or '')[:15]
        user_type = data.get('user_type')

        if not full_name or not email or not password or not user_type:
            return JsonResponse({'status': 'error', 'message': 'All fields are required.'}, status=400)

        if Users.objects.filter(email=email).exists():
            return JsonResponse({'status': 'error', 'message': 'A user with this email already exists.'}, status=400)

        max_id = Users.objects.all().order_by('-user_id').first()
        next_id = (max_id.user_id + 1) if max_id else 1

        user = Users.objects.create(
            user_id=next_id,
            full_name=full_name,
            email=email,
            password=password,
            user_type=user_type
        )

        if user_type == 'InterviewPanelMember':
            _create_interview_panel_if_needed(full_name)

        return JsonResponse({
            'status': 'success',
            'message': 'User created successfully!',
            'user': {'user_id': user.user_id, 'full_name': user.full_name}
        }, status=201)

    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON.'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


def api_applicant_list(request):
    applicants = Applicants.objects.select_related('user').all().order_by('applicant_id')
    data = []
    for a in applicants:
        data.append({
            'applicant_id': a.applicant_id,
            'user_id': a.user.user_id if a.user else None,
            'full_name': a.user.full_name if a.user else 'N/A',
            'email': a.user.email if a.user else 'N/A',
            'date_of_birth': str(a.date_of_birth) if a.date_of_birth else '',
            'gender': a.gender or '',
            'phone_number': a.phone_number or '',
            'address': a.address or ''
        })
    return JsonResponse({'status': 'success', 'applicants': data})


@csrf_exempt
@require_http_methods(["POST"])
def api_applicant_create(request):
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        date_of_birth = data.get('date_of_birth')
        gender = data.get('gender')
        phone_number = data.get('phone_number')
        address = data.get('address')

        if not user_id:
            return JsonResponse({'status': 'error', 'message': 'User selection is required.'}, status=400)

        try:
            user = Users.objects.get(pk=user_id)
        except Users.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Invalid User ID.'}, status=400)

        if Applicants.objects.filter(user=user).exists():
            return JsonResponse({'status': 'error', 'message': 'An applicant profile for this user already exists.'}, status=400)

        max_id = Applicants.objects.all().order_by('-applicant_id').first()
        next_id = (max_id.applicant_id + 1) if max_id else 1

        applicant = Applicants.objects.create(
            applicant_id=next_id,
            user=user,
            date_of_birth=date_of_birth if date_of_birth else None,
            gender=gender or None,
            phone_number=phone_number or None,
            address=address or None
        )

        return JsonResponse({
            'status': 'success',
            'message': 'Applicant profile created successfully!',
            'applicant': {'applicant_id': applicant.applicant_id, 'full_name': applicant.user.full_name if applicant.user else 'N/A'}
        }, status=201)

    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON data.'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["PUT"])
def api_applicant_update(request, applicant_id):
    try:
        try:
            applicant = Applicants.objects.get(pk=applicant_id)
        except Applicants.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Applicant not found.'}, status=404)

        data = json.loads(request.body)
        user_id = data.get('user_id')
        date_of_birth = data.get('date_of_birth')
        gender = data.get('gender')
        phone_number = data.get('phone_number')
        address = data.get('address')

        if not user_id:
            return JsonResponse({'status': 'error', 'message': 'User selection is required.'}, status=400)

        try:
            user = Users.objects.get(pk=user_id)
        except Users.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Invalid User ID.'}, status=400)

        if Applicants.objects.filter(user=user).exclude(pk=applicant_id).exists():
            return JsonResponse({'status': 'error', 'message': 'Another applicant profile already uses this user.'}, status=400)

        applicant.user = user
        applicant.date_of_birth = date_of_birth if date_of_birth else None
        applicant.gender = gender or None
        applicant.phone_number = phone_number or None
        applicant.address = address or None
        applicant.save()

        return JsonResponse({'status': 'success', 'message': 'Applicant profile updated successfully!'})
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON.'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
def api_applicant_delete(request, applicant_id):
    try:
        try:
            applicant = Applicants.objects.get(pk=applicant_id)
        except Applicants.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Applicant not found.'}, status=404)

        applicant.delete()
        return JsonResponse({'status': 'success', 'message': f'Applicant {applicant_id} deleted successfully.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
def api_user_delete(request, user_id):
    try:
        try:
            user = Users.objects.get(pk=user_id)
        except Users.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'User not found.'}, status=404)

        user.delete()
        return JsonResponse({'status': 'success', 'message': f'User {user_id} deleted successfully.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


def api_job_list(request):
    jobs = JobPostings.objects.select_related('department').all().order_by('job_id')
    data = []
    for job in jobs:
        data.append({
            'job_id': job.job_id,
            'title': job.title,
            'description': job.description,
            'department_name': job.department.department_name if job.department else 'N/A',
            'department_id': job.department.department_id if job.department else None,
            'posted_date': str(job.posted_date) if job.posted_date else '',
            'closing_date': str(job.closing_date) if job.closing_date else ''
        })
    return JsonResponse({'status': 'success', 'jobs': data})


@csrf_exempt
@require_http_methods(["POST"])
def api_job_create(request):
    try:
        data = json.loads(request.body)
        title = data.get('title')
        description = data.get('description')
        department_id = data.get('department')
        posted_date = data.get('posted_date')
        closing_date = data.get('closing_date')

        if not title or not department_id:
            return JsonResponse({'status': 'error', 'message': 'Title and Department are required fields.'}, status=400)

        try:
            department = Departments.objects.get(pk=department_id)
        except Departments.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Invalid Department ID.'}, status=400)

        max_id = JobPostings.objects.all().order_by('-job_id').first()
        next_id = (max_id.job_id + 1) if max_id else 1

        job = JobPostings.objects.create(
            job_id=next_id,
            title=title,
            description=description,
            department=department,
            posted_date=posted_date if posted_date else None,
            closing_date=closing_date if closing_date else None
        )

        return JsonResponse({
            'status': 'success',
            'message': 'Job posting created successfully!',
            'job': {'job_id': job.job_id, 'title': job.title}
        }, status=201)

    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON data payload.'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
def api_job_delete(request, job_id):
    try:
        try:
            job = JobPostings.objects.get(pk=job_id)
        except JobPostings.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Job posting not found.'}, status=404)

        job.delete()
        return JsonResponse({'status': 'success', 'message': f'Job {job_id} deleted successfully.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["PUT"])
def api_user_update(request, user_id):
    try:
        try:
            user = Users.objects.get(pk=user_id)
        except Users.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'User not found.'}, status=404)

        data = json.loads(request.body)
        full_name = data.get('full_name')
        email = data.get('email')
        password = data.get('password')
        user_type = data.get('user_type')

        if not full_name or not email or not user_type:
            return JsonResponse({'status': 'error', 'message': 'Full Name, Email, and Role are required.'}, status=400)

        if Users.objects.filter(email=email).exclude(pk=user_id).exists():
            return JsonResponse({'status': 'error', 'message': 'A user with this email already exists.'}, status=400)

        user.full_name = full_name
        user.email = email
        user.user_type = user_type
        if password:
            user.password = password[:15]

        user.save()
        return JsonResponse({'status': 'success', 'message': 'User profile updated successfully!'})
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON.'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["PUT"])
def api_job_update(request, job_id):
    try:
        try:
            job = JobPostings.objects.get(pk=job_id)
        except JobPostings.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Job posting not found.'}, status=404)

        data = json.loads(request.body)
        title = data.get('title')
        description = data.get('description')
        department_id = data.get('department')
        posted_date = data.get('posted_date')
        closing_date = data.get('closing_date')

        if not title or not department_id:
            return JsonResponse({'status': 'error', 'message': 'Title and Department are required.'}, status=400)

        try:
            department = Departments.objects.get(pk=department_id)
        except Departments.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Invalid Department ID.'}, status=400)

        job.title = title
        job.description = description
        job.department = department
        job.posted_date = posted_date if posted_date else None
        job.closing_date = closing_date if closing_date else None
        job.save()

        return JsonResponse({'status': 'success', 'message': 'Job posting updated successfully!'})
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON.'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


# ========== APPLICATIONS API ==========

def api_application_list(request):
    applications = Applications.objects.select_related('applicant__user', 'job__department').all().order_by('-application_id')
    data = []
    for app in applications:
        data.append({
            'application_id': app.application_id,
            'applicant_id': app.applicant.applicant_id if app.applicant else None,
            'applicant_name': app.applicant.user.full_name if app.applicant and app.applicant.user else 'N/A',
            'job_id': app.job.job_id if app.job else None,
            'job_title': app.job.title if app.job else 'N/A',
            'application_date': str(app.application_date) if app.application_date else '',
            'status': app.status or '',
        })
    return JsonResponse({'status': 'success', 'applications': data})


@csrf_exempt
@require_http_methods(["POST"])
def api_application_create(request):
    try:
        data = json.loads(request.body)
        applicant_id = data.get('applicant_id')
        job_id = data.get('job_id')
        application_date = data.get('application_date')
        status = data.get('status', 'Pending')

        if not applicant_id or not job_id:
            return JsonResponse({'status': 'error', 'message': 'Applicant and Job are required.'}, status=400)

        try:
            applicant = Applicants.objects.get(pk=applicant_id)
        except Applicants.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Invalid Applicant ID.'}, status=400)

        try:
            job = JobPostings.objects.get(pk=job_id)
        except JobPostings.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Invalid Job ID.'}, status=400)

        if Applications.objects.filter(applicant=applicant, job=job).exists():
            return JsonResponse({'status': 'error', 'message': 'This applicant has already applied for this job.'}, status=400)

        max_id = Applications.objects.all().order_by('-application_id').first()
        next_id = (max_id.application_id + 1) if max_id else 1

        app = Applications.objects.create(
            application_id=next_id,
            applicant=applicant,
            job=job,
            application_date=application_date if application_date else date.today(),
            status=status
        )

        try:
            user = applicant.user
            if user:
                send_application_confirmation(user.email, user.full_name, job.title)
        except Exception:
            pass

        return JsonResponse({
            'status': 'success',
            'message': 'Application created successfully!',
            'application': {'application_id': app.application_id}
        }, status=201)

    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON.'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["PUT"])
def api_application_update(request, application_id):
    try:
        try:
            app = Applications.objects.get(pk=application_id)
        except Applications.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Application not found.'}, status=404)

        data = json.loads(request.body)
        applicant_id = data.get('applicant_id')
        job_id = data.get('job_id')
        application_date = data.get('application_date')
        status = data.get('status')

        if not applicant_id or not job_id:
            return JsonResponse({'status': 'error', 'message': 'Applicant and Job are required.'}, status=400)

        try:
            applicant = Applicants.objects.get(pk=applicant_id)
        except Applicants.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Invalid Applicant ID.'}, status=400)

        try:
            job = JobPostings.objects.get(pk=job_id)
        except JobPostings.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Invalid Job ID.'}, status=400)

        if Applications.objects.filter(applicant=applicant, job=job).exclude(pk=application_id).exists():
            return JsonResponse({'status': 'error', 'message': 'Another application already exists for this applicant and job.'}, status=400)

        app.applicant = applicant
        app.job = job
        app.application_date = application_date if application_date else None
        app.status = status or 'Pending'
        app.save()

        return JsonResponse({'status': 'success', 'message': 'Application updated successfully!'})
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON.'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
def api_application_delete(request, application_id):
    try:
        try:
            app = Applications.objects.get(pk=application_id)
        except Applications.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Application not found.'}, status=404)

        app.delete()
        return JsonResponse({'status': 'success', 'message': f'Application {application_id} deleted successfully.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


# ========== PROFILE API (JobApplicant) ==========

@csrf_exempt
@role_required(['JobApplicant'])
@require_http_methods(["PUT"])
def api_update_profile(request):
    try:
        user_id = request.session.get('user_id')
        applicant = Applicants.objects.filter(user_id=user_id).first()
        data = json.loads(request.body)

        date_of_birth = data.get('date_of_birth')
        gender = data.get('gender')
        phone_number = data.get('phone_number')
        address = data.get('address')

        if applicant:
            applicant.date_of_birth = date_of_birth if date_of_birth else None
            applicant.gender = gender or None
            applicant.phone_number = phone_number or None
            applicant.address = address or None
            applicant.save()
            return JsonResponse({'status': 'success', 'message': 'Profile updated successfully!'})
        else:
            max_id = Applicants.objects.order_by('-applicant_id').first()
            next_id = (max_id.applicant_id + 1) if max_id else 1
            Applicants.objects.create(
                applicant_id=next_id,
                user_id=user_id,
                date_of_birth=date_of_birth if date_of_birth else None,
                gender=gender or None,
                phone_number=phone_number or None,
                address=address or None
            )
            return JsonResponse({'status': 'success', 'message': 'Profile created successfully!'}, status=201)

    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON.'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


# ========== QUALIFICATIONS API ==========

@csrf_exempt
@role_required(['JobApplicant'])
@require_http_methods(["POST"])
def api_qualification_create(request):
    try:
        data = json.loads(request.body)
        user_id = request.session.get('user_id')
        applicant = Applicants.objects.filter(user_id=user_id).first()
        if not applicant:
            return JsonResponse({'status': 'error', 'message': 'Please create your profile first.'}, status=400)

        institution = data.get('institution', '').strip()
        award = data.get('award', '').strip()
        year_completed = data.get('year_completed')

        if not institution or not award:
            return JsonResponse({'status': 'error', 'message': 'Institution and Award are required.'}, status=400)

        max_id = Qualifications.objects.order_by('-qualification_id').first()
        next_id = (max_id.qualification_id + 1) if max_id else 1

        qual = Qualifications.objects.create(
            qualification_id=next_id,
            applicant=applicant,
            institution=institution,
            award=award,
            year_completed=year_completed if year_completed else None
        )
        return JsonResponse({
            'status': 'success',
            'message': 'Qualification added successfully!',
            'qualification': {
                'qualification_id': qual.qualification_id,
                'institution': qual.institution,
                'award': qual.award,
                'year_completed': qual.year_completed,
            }
        }, status=201)
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON.'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
@role_required(['JobApplicant'])
@require_http_methods(["PUT"])
def api_qualification_update(request, qualification_id):
    try:
        user_id = request.session.get('user_id')
        applicant = Applicants.objects.filter(user_id=user_id).first()
        if not applicant:
            return JsonResponse({'status': 'error', 'message': 'Applicant profile not found.'}, status=400)

        try:
            qual = Qualifications.objects.get(pk=qualification_id, applicant=applicant)
        except Qualifications.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Qualification not found.'}, status=404)

        data = json.loads(request.body)
        qual.institution = data.get('institution', qual.institution)
        qual.award = data.get('award', qual.award)
        qual.year_completed = data.get('year_completed', qual.year_completed)
        qual.save()

        return JsonResponse({'status': 'success', 'message': 'Qualification updated successfully!'})
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON.'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
@role_required(['JobApplicant'])
@require_http_methods(["DELETE"])
def api_qualification_delete(request, qualification_id):
    try:
        user_id = request.session.get('user_id')
        applicant = Applicants.objects.filter(user_id=user_id).first()
        if not applicant:
            return JsonResponse({'status': 'error', 'message': 'Applicant profile not found.'}, status=400)

        try:
            qual = Qualifications.objects.get(pk=qualification_id, applicant=applicant)
        except Qualifications.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Qualification not found.'}, status=404)

        qual.delete()
        return JsonResponse({'status': 'success', 'message': 'Qualification deleted successfully.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


# ========== APPLICANT SKILLS API ==========

@csrf_exempt
@role_required(['JobApplicant'])
@require_http_methods(["POST"])
def api_applicant_skill_create(request):
    try:
        data = json.loads(request.body)
        user_id = request.session.get('user_id')
        applicant = Applicants.objects.filter(user_id=user_id).first()
        if not applicant:
            return JsonResponse({'status': 'error', 'message': 'Please create your profile first.'}, status=400)

        skill_id = data.get('skill_id')
        skill_name = data.get('skill_name', '').strip()
        proficiency_level = data.get('proficiency_level', 'Intermediate')

        if skill_id:
            try:
                skill = Skills.objects.get(pk=skill_id)
            except Skills.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Invalid Skill ID.'}, status=400)
        elif skill_name:
            max_skill_id = Skills.objects.order_by('-skill_id').first()
            next_skill_id = (max_skill_id.skill_id + 1) if max_skill_id else 1
            skill, _ = Skills.objects.get_or_create(
                skill_name=skill_name,
                defaults={'skill_id': next_skill_id}
            )
        else:
            return JsonResponse({'status': 'error', 'message': 'Skill is required.'}, status=400)

        if ApplicantSkills.objects.filter(applicant=applicant, skill=skill).exists():
            return JsonResponse({'status': 'error', 'message': 'You have already added this skill.'}, status=400)

        max_id = ApplicantSkills.objects.order_by('-applicant_skill_id').first()
        next_id = (max_id.applicant_skill_id + 1) if max_id else 1

        app_skill = ApplicantSkills.objects.create(
            applicant_skill_id=next_id,
            applicant=applicant,
            skill=skill,
            proficiency_level=proficiency_level
        )
        return JsonResponse({
            'status': 'success',
            'message': 'Skill added successfully!',
            'applicant_skill': {
                'applicant_skill_id': app_skill.applicant_skill_id,
                'skill_id': skill.skill_id,
                'skill_name': skill.skill_name,
                'proficiency_level': app_skill.proficiency_level,
            }
        }, status=201)
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON.'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
@role_required(['JobApplicant'])
@require_http_methods(["PUT"])
def api_applicant_skill_update(request, applicant_skill_id):
    try:
        user_id = request.session.get('user_id')
        applicant = Applicants.objects.filter(user_id=user_id).first()
        if not applicant:
            return JsonResponse({'status': 'error', 'message': 'Applicant profile not found.'}, status=400)

        try:
            app_skill = ApplicantSkills.objects.get(pk=applicant_skill_id, applicant=applicant)
        except ApplicantSkills.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Skill entry not found.'}, status=404)

        data = json.loads(request.body)
        skill_id = data.get('skill_id')
        skill_name = data.get('skill_name', '').strip()
        proficiency_level = data.get('proficiency_level')

        if skill_id:
            try:
                skill = Skills.objects.get(pk=skill_id)
            except Skills.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Invalid Skill ID.'}, status=400)
            if ApplicantSkills.objects.filter(applicant=applicant, skill=skill).exclude(pk=applicant_skill_id).exists():
                return JsonResponse({'status': 'error', 'message': 'You have already added this skill.'}, status=400)
            app_skill.skill = skill
        elif skill_name:
            max_skill_id = Skills.objects.order_by('-skill_id').first()
            next_skill_id = (max_skill_id.skill_id + 1) if max_skill_id else 1
            skill, _ = Skills.objects.get_or_create(
                skill_name=skill_name,
                defaults={'skill_id': next_skill_id}
            )
            if ApplicantSkills.objects.filter(applicant=applicant, skill=skill).exclude(pk=applicant_skill_id).exists():
                return JsonResponse({'status': 'error', 'message': 'You have already added this skill.'}, status=400)
            app_skill.skill = skill

        if proficiency_level:
            app_skill.proficiency_level = proficiency_level

        app_skill.save()
        return JsonResponse({'status': 'success', 'message': 'Skill updated successfully!'})
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON.'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
@role_required(['JobApplicant'])
@require_http_methods(["DELETE"])
def api_applicant_skill_delete(request, applicant_skill_id):
    try:
        user_id = request.session.get('user_id')
        applicant = Applicants.objects.filter(user_id=user_id).first()
        if not applicant:
            return JsonResponse({'status': 'error', 'message': 'Applicant profile not found.'}, status=400)

        try:
            app_skill = ApplicantSkills.objects.get(pk=applicant_skill_id, applicant=applicant)
        except ApplicantSkills.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Skill entry not found.'}, status=404)

        app_skill.delete()
        return JsonResponse({'status': 'success', 'message': 'Skill removed successfully.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


# ========== PRINT PROFILE (Applicant) ==========

@role_required(['JobApplicant'])
def print_profile(request):
    user_id = request.session.get('user_id')
    user = Users.objects.get(pk=user_id)
    applicant = Applicants.objects.filter(user_id=user_id).first()
    qualifications = Qualifications.objects.filter(applicant=applicant).order_by('-year_completed') if applicant else []
    skills_list = ApplicantSkills.objects.filter(applicant=applicant).select_related('skill') if applicant else []
    applications = Applications.objects.filter(applicant=applicant).select_related('job__department').all() if applicant else []

    context = {
        'user': user,
        'applicant': applicant,
        'qualifications': qualifications,
        'skills_list': skills_list,
        'applications': applications,
    }
    return render(request, 'profile/print_profile.html', context)


# ========== DEPARTMENT MANAGEMENT (HR) ==========

@role_required(['HumanResourceOfficer'])
def departments_view(request):
    departments_list = Departments.objects.annotate(job_count=Count('jobpostings')).order_by('department_id')
    context = {
        'active_tab': 'departments',
        'departments': departments_list,
    }
    return render(request, 'departments/departments.html', context)


@role_required(['HumanResourceOfficer'])
def department_add(request):
    if request.method == 'POST':
        dept_name = request.POST.get('department_name', '').strip()
        description = request.POST.get('description', '').strip()

        if not dept_name:
            messages.error(request, 'Department name is required.')
            return render(request, 'departments/add_department.html', {'active_tab': 'departments'})

        max_id = Departments.objects.order_by('-department_id').first()
        next_id = (max_id.department_id + 1) if max_id else 1

        Departments.objects.create(
            department_id=next_id,
            department_name=dept_name,
            description=description or None,
        )
        messages.success(request, f'Department "{dept_name}" created successfully.')
        return redirect('recruitmentapp:departments')

    return render(request, 'departments/add_department.html', {'active_tab': 'departments'})


@role_required(['HumanResourceOfficer'])
def department_edit(request, department_id):
    try:
        dept = Departments.objects.get(pk=department_id)
    except Departments.DoesNotExist:
        messages.error(request, 'Department not found.')
        return redirect('recruitmentapp:departments')

    if request.method == 'POST':
        dept_name = request.POST.get('department_name', '').strip()
        description = request.POST.get('description', '').strip()

        if not dept_name:
            messages.error(request, 'Department name is required.')
            return render(request, 'departments/edit_department.html', {
                'active_tab': 'departments',
                'department': dept,
            })

        dept.department_name = dept_name
        dept.description = description or None
        dept.save()
        messages.success(request, f'Department "{dept_name}" updated successfully.')
        return redirect('recruitmentapp:departments')

    return render(request, 'departments/edit_department.html', {
        'active_tab': 'departments',
        'department': dept,
    })


@role_required(['HumanResourceOfficer'])
def department_delete(request, department_id):
    try:
        dept = Departments.objects.get(pk=department_id)
    except Departments.DoesNotExist:
        messages.error(request, 'Department not found.')
        return redirect('recruitmentapp:departments')

    jobs_count = JobPostings.objects.filter(department=dept).count()
    if jobs_count > 0:
        messages.error(request, f'Cannot delete "{dept.department_name}" — {jobs_count} job posting(s) are linked to it.')
        return redirect('recruitmentapp:departments')

    dept_name = dept.department_name
    dept.delete()
    messages.success(request, f'Department "{dept_name}" deleted successfully.')
    return redirect('recruitmentapp:departments')


@role_required(['HumanResourceOfficer'])
def department_jobs(request, department_id):
    try:
        dept = Departments.objects.get(pk=department_id)
    except Departments.DoesNotExist:
        messages.error(request, 'Department not found.')
        return redirect('recruitmentapp:departments')

    jobs = JobPostings.objects.filter(department=dept).order_by('-job_id')
    context = {
        'active_tab': 'departments',
        'department': dept,
        'jobs': jobs,
    }
    return render(request, 'departments/department_jobs.html', context)


# ========== PANEL MEMBER MANAGEMENT (HR) ==========

@role_required(['HumanResourceOfficer'])
def panel_members_view(request):
    all_panel_members = InterviewPanel.objects.all().order_by('full_name')
    departments = Departments.objects.all().order_by('department_name')

    enriched = []
    for pm in all_panel_members:
        interviewer_prefix = f'Interviewer: {pm.full_name}'
        assigned_count = Interviews.objects.filter(remarks__startswith=interviewer_prefix).count()
        completed_count = Interviews.objects.filter(
            remarks__startswith=interviewer_prefix, score__isnull=False
        ).count()
        enriched.append({
            'panel': pm,
            'assigned': assigned_count,
            'completed': completed_count,
        })

    context = {
        'active_tab': 'panel_members',
        'panel_members': enriched,
        'departments': departments,
    }
    return render(request, 'panel_members/panel_members.html', context)


@role_required(['HumanResourceOfficer'])
def panel_member_assign_department(request, panel_id):
    if request.method == 'POST':
        department_id = request.POST.get('department_id')
        try:
            pm = InterviewPanel.objects.get(pk=panel_id)
        except InterviewPanel.DoesNotExist:
            messages.error(request, 'Panel member not found.')
            return redirect('recruitmentapp:panel_members')

        if department_id:
            try:
                dept = Departments.objects.get(pk=department_id)
                pm.department = dept
            except Departments.DoesNotExist:
                messages.error(request, 'Department not found.')
                return redirect('recruitmentapp:panel_members')
        else:
            pm.department = None
        pm.save()
        messages.success(request, f'{pm.full_name}\'s department updated.')
    return redirect('recruitmentapp:panel_members')


# ========== INTERVIEWER PROFILE ==========

def _interviewer_profile_context(panel_member, user=None):
    departments = Departments.objects.all().order_by('department_name')
    interviewer_prefix = f'Interviewer: {panel_member.full_name}' if panel_member else ''
    assigned_interviews = Interviews.objects.filter(remarks__startswith=interviewer_prefix) if panel_member else Interviews.objects.none()
    total_assigned = assigned_interviews.count()
    completed_count = assigned_interviews.exclude(score__isnull=True).count()
    pending_count = total_assigned - completed_count
    return {
        'panel_member': panel_member,
        'user': user or (panel_member and hasattr(panel_member, 'user') and panel_member.user),
        'departments': departments,
        'total_assigned': total_assigned,
        'completed_count': completed_count,
        'pending_count': pending_count,
    }


@role_required(['InterviewPanelMember'])
def interviewer_profile(request):
    user_id = request.session.get('user_id')
    user = Users.objects.get(pk=user_id)
    panel_member = InterviewPanel.objects.filter(full_name=user.full_name).first()
    if not panel_member and user.user_type == 'InterviewPanelMember':
        _create_interview_panel_if_needed(user.full_name)
        panel_member = InterviewPanel.objects.filter(full_name=user.full_name).first()
    departments = Departments.objects.all().order_by('department_name')

    if request.method == 'POST':
        department_id = request.POST.get('department_id')
        if panel_member:
            if department_id:
                try:
                    dept = Departments.objects.get(pk=department_id)
                    panel_member.department = dept
                except Departments.DoesNotExist:
                    messages.error(request, 'Department not found.')
                    return redirect('recruitmentapp:interviewer_profile')
            else:
                panel_member.department = None
            panel_member.save()
            messages.success(request, 'Your department has been updated.')
        else:
            messages.error(request, 'Your account is not linked to an interviewer profile.')
        return redirect('recruitmentapp:interviewer_profile')

    context = _interviewer_profile_context(panel_member, user)
    context['active_tab'] = 'interviewer_profile'
    return render(request, 'dashboards/interviewer_profile.html', context)


@role_required(['HumanResourceOfficer'])
def panel_member_detail(request, panel_id):
    try:
        panel_member = InterviewPanel.objects.get(pk=panel_id)
    except InterviewPanel.DoesNotExist:
        messages.error(request, 'Panel member not found.')
        return redirect('recruitmentapp:panel_members')

    context = _interviewer_profile_context(panel_member)
    context['active_tab'] = 'panel_members'
    context['is_hr_view'] = True
    return render(request, 'dashboards/interviewer_profile.html', context)
