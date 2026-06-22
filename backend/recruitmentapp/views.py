from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from functools import wraps
import json
from .models import JobPostings, Departments, Users, Applicants, Applications


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
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        user_type = request.POST.get('user_type', '').strip()

        if not all([full_name, email, password, confirm_password, user_type]):
            messages.error(request, 'All fields are required.')
            return render(request, 'authentication/signup.html')

        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'authentication/signup.html')

        if Users.objects.filter(email=email).exists():
            messages.error(request, 'A user with this email already exists.')
            return render(request, 'authentication/signup.html')

        max_id = Users.objects.order_by('-user_id').first()
        next_id = (max_id.user_id + 1) if max_id else 1

        Users.objects.create(
            user_id=next_id,
            full_name=full_name,
            email=email,
            password=password,
            user_type=user_type
        )

        messages.success(request, 'Account created successfully! Please log in.')
        return redirect('recruitmentapp:signin')

    return render(request, 'authentication/signup.html')


def signin_view(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        if not all([email, password]):
            messages.error(request, 'All fields are required.')
            return render(request, 'authentication/signin.html')

        user = Users.objects.filter(email=email).first()
        if not user or user.password != password:
            messages.error(request, 'Invalid credentials.')
            return render(request, 'authentication/signin.html')

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
    context = {
        'active_tab': 'dashboard',
    }
    return render(request, 'dashboards/panel_dashboard.html', context)


@role_required(['JobApplicant'])
def applicant_dashboard(request):
    user_id = request.session.get('user_id')
    applicant = Applicants.objects.filter(user_id=user_id).first()
    applications = []
    if applicant:
        applications = Applications.objects.filter(applicant=applicant).select_related('job').all()
    context = {
        'active_tab': 'dashboard',
        'applicant': applicant,
        'applications': applications,
        'total_applications': len(applications),
    }
    return render(request, 'dashboards/applicant_dashboard.html', context)


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

    context = {
        'applications': applications_list,
        'active_tab': 'applications',
    }
    return render(request, 'applications/applications.html', context)


# ========== API ENDPOINTS (unchanged) ==========

@csrf_exempt
@require_http_methods(["POST"])
def api_signup(request):
    try:
        data = json.loads(request.body)
        full_name = data.get('full_name', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        user_type = data.get('user_type', '').strip()

        if not full_name or not email or not password or not user_type:
            return JsonResponse({'status': 'error', 'message': 'All fields are required.'}, status=400)

        if Users.objects.filter(email=email).exists():
            return JsonResponse({'status': 'error', 'message': 'A user with this email already exists.'}, status=400)

        max_id = Users.objects.order_by('-user_id').first()
        next_id = (max_id.user_id + 1) if max_id else 1

        Users.objects.create(
            user_id=next_id,
            full_name=full_name,
            email=email,
            password=password,
            user_type=user_type
        )

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
        password = data.get('password')
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
            user.password = password

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
