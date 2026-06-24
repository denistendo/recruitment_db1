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
        f'Human Resource Team'
    )
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[user_email],
        fail_silently=False,
    )


def send_interview_scheduled(user_email, full_name, job_title, interview_date, interview_time, interview_mode):
    subject = 'Interview Scheduled — Recruitment Platform'
    time_line = f'  - Time: {interview_time}\n' if interview_time else ''
    message = (
        f'Dear {full_name},\n\n'
        f'We are pleased to inform you that an interview has been scheduled for your application for the position:\n'
        f'  "{job_title}"\n\n'
        f'Interview Details:\n'
        f'  - Date: {interview_date}\n'
        f'{time_line}'
        f'  - Mode: {interview_mode}\n\n'
        f'Please make sure to be available at the scheduled time. '
        f'If you have any questions or need to reschedule, please contact our recruitment team.\n\n'
        f'Best regards,\n'
        f'Human Resource Team'
    )
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[user_email],
        fail_silently=False,
    )


def send_interviewed(user_email, full_name, job_title):
    subject = 'Interview Completed — Recruitment Platform'
    message = (
        f'Dear {full_name},\n\n'
        f'Thank you for attending the interview for the position:\n'
        f'  "{job_title}"\n\n'
        f'Your interview has been completed successfully. Our recruitment team is now reviewing your results.\n\n'
        f'You will be contacted via email or telephone with further details regarding the outcome.\n\n'
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


def send_rejected(user_email, full_name, job_title):
    subject = 'Application Update — Recruitment Platform'
    message = (
        f'Dear {full_name},\n\n'
        f'Thank you for your interest in the position:\n'
        f'  "{job_title}"\n\n'
        f'After careful consideration, we regret to inform you that your application has not been successful at this time.\n\n'
        f'We appreciate the time and effort you put into your application and wish you all the best in your future endeavors.\n\n'
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


def send_password_reset_code(user_email, full_name, reset_code):
    subject = 'Password Reset Code — Recruitment Platform'
    message = (
        f'Dear {full_name},\n\n'
        f'You have requested to reset your password for the Recruitment Platform.\n\n'
        f'Your password reset code is:\n\n'
        f'  {reset_code}\n\n'
        f'This code will expire in 10 minutes.\n\n'
        f'If you did not request this, please ignore this email.\n\n'
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


def send_accepted(user_email, full_name, job_title):
    subject = 'Congratulations! Application Accepted — Recruitment Platform'
    message = (
        f'Dear {full_name},\n\n'
        f'Congratulations! We are delighted to inform you that your application for the position:\n'
        f'  "{job_title}"\n\n'
        f'has been accepted. We were impressed with your qualifications and experience, '
        f'and we are excited to welcome you to the team.\n\n'
        f'Next Steps:\n'
        f'  - Our HR team will reach out to you within 3-5 business days with further instructions.\n'
        f'  - You will receive details regarding onboarding, documentation, and start date.\n'
        f'  - If you have any questions in the meantime, please reply to this email.\n\n'
        f'We look forward to having you on board!\n\n'
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
