from django.core.mail import send_mail
from django.conf import settings


def send_application_confirmation(user_email, full_name, job_title, phone_number=None):
    subject = 'Application Received — Recruitment Platform'
    contact_info = f'  - Contact Email: {user_email}\n'
    if phone_number:
        contact_info += f'  - Contact Phone: {phone_number}\n'
    message = (
        f'Dear {full_name},\n\n'
        f'Thank you for submitting your application for the position:\n'
        f'  "{job_title}"\n\n'
        f'We have successfully received your application. Here is a quick summary:\n'
        f'  - Position: {job_title}\n'
        f'  - Applicant: {full_name}\n'
        f'{contact_info}'
        f'\n'
        f'Our recruitment team will review your qualifications and experience. '
        f'You will be contacted via email or telephone with further details regarding the next steps.\n\n'
        f'If you have any questions in the meantime, please do not hesitate to reach out.\n\n'
        f'Best regards,\n'
        f'Recruitment Team'
    )
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[user_email],
        fail_silently=False,
    )
