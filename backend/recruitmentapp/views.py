from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from .models import JobPostings, Departments, Users

# ==============================================================================
# Django Views for CRUD Operations
# Purpose:
#   Views act as the controller logic. They receive HTTP requests from the browser,
#   query or modify the SQL Server database via Django models, and return a response.
#   We use two kinds of responses here:
#     1. HTML Responses (via `render`): To draw the initial dashboard skeleton.
#     2. JSON Responses (via `JsonResponse`): To send database updates to the client
#        in the background (AJAX) without reloading the page.
# ==============================================================================


def dashboard_index(request):

    # Fetch all jobs, departments, and users from the database
    jobs = JobPostings.objects.select_related('department').all().order_by('-job_id')
    departments = Departments.objects.all().order_by('department_name')
    users = Users.objects.all().order_by('-user_id')
    
    context = {
        'jobs': jobs,
        'departments': departments,
        'users': users
    }
    return render(request, 'recruitmentapp/dashboard.html', context)


# ==============================================================================
# USERS CRUD API ENDPOINTS
# ==============================================================================

def api_user_list(request):

    users = Users.objects.all().order_by('-user_id')
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
        
        # 1. Validation
        if not full_name or not email or not password or not user_type:
            return JsonResponse({'status': 'error', 'message': 'All fields are required.'}, status=400)
            
        # 2. Email uniqueness check
        if Users.objects.filter(email=email).exists():
            return JsonResponse({'status': 'error', 'message': 'A user with this email already exists.'}, status=400)
            
        # 3. Determine next ID
        max_id = Users.objects.all().order_by('-user_id').first()
        next_id = (max_id.user_id + 1) if max_id else 1
        
        # 4. Save User
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
            'user': {
                'user_id': user.user_id,
                'full_name': user.full_name
            }
        }, status=201)
        
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON data.'}, status=400)
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


# ==============================================================================
# JOB POSTINGS CRUD API ENDPOINTS
# ==============================================================================

def api_job_list(request):

    jobs = JobPostings.objects.select_related('department').all().order_by('-job_id')
    data = []
    for job in jobs:
        data.append({
            'job_id': job.job_id,
            'title': job.title,
            'description': job.description,
            'department_name': job.department.department_name if job.department else 'N/A',
            'posted_date': str(job.posted_date) if job.posted_date else '',
            'closing_date': str(job.closing_date) if job.closing_date else ''
        })
    return JsonResponse({'status': 'success', 'jobs': data})


@csrf_exempt
@require_http_methods(["POST"])
def api_job_create(request):

    try:
        data = json.loads(request.body)
        
        # 1. Validate mandatory fields
        title = data.get('title')
        description = data.get('description')
        department_id = data.get('department')
        posted_date = data.get('posted_date')
        closing_date = data.get('closing_date')
        
        if not title or not department_id:
            return JsonResponse({'status': 'error', 'message': 'Title and Department are required fields.'}, status=400)
        
        # 2. Get Department instance
        try:
            department = Departments.objects.get(pk=department_id)
        except Departments.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Invalid Department ID.'}, status=400)
            
        # 3. Determine next Job ID
        max_id = JobPostings.objects.all().order_by('-job_id').first()
        next_id = (max_id.job_id + 1) if max_id else 1
        
        # 4. Save to Database
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
            'job': {
                'job_id': job.job_id,
                'title': job.title
            }
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

