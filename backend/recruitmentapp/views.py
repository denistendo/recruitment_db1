from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from .models import JobPostings, Departments

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
    """
    Purpose: Renders the primary dashboard HTML page.
    Relevance:
      - This is the initial entry point when the user visits the home page.
      - We query the database to get all Job Postings and all Departments.
      - The lists are passed into the HTML template context so they can be 
        rendered server-side on initial load.
    """
    # Fetch all job postings from the database
    # (Notice: select_related fetches the related Department data in a single query
    # to avoid the N+1 database query performance issue)
    jobs = JobPostings.objects.select_related('department').all().order_by('-job_id')
    departments = Departments.objects.all().order_by('department_name')
    
    context = {
        'jobs': jobs,
        'departments': departments
    }
    return render(request, 'recruitmentapp/dashboard.html', context)


def api_job_list(request):
    """
    Purpose: Returns all jobs as JSON.
    Relevance:
      - Used by JavaScript to dynamically reload the list of job postings after 
        a creation or deletion without refreshing the entire page.
    """
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
    """
    Purpose: Creates a new Job Posting in the database from an AJAX request.
    Relevance:
      - The javascript app will send a POST request with JSON payload.
      - We parse the data, validate required fields, query the related Department,
        and save the record to the SQL Server database.
      - Returns JSON success/error message.
    """
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
            
        # 3. Determine next Job ID (needed since database table may not have auto-increment enabled)
        # We query the highest current ID and add 1.
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
    """
    Purpose: Deletes a specific Job Posting from the database.
    Relevance:
      - The javascript app sends a DELETE request to `/api/jobs/delete/<job_id>/`.
      - We query the object and delete it.
      - Returns success response to the client.
    """
    try:
        try:
            job = JobPostings.objects.get(pk=job_id)
        except JobPostings.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Job posting not found.'}, status=44)
            
        job.delete()
        return JsonResponse({'status': 'success', 'message': f'Job {job_id} deleted successfully.'})
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
