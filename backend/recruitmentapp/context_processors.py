from .models import Users


def session_user(request):
    user = None
    user_id = request.session.get('user_id')
    if user_id:
        try:
            user = Users.objects.get(pk=user_id)
        except Users.DoesNotExist:
            pass
    return {'session_user': user}
