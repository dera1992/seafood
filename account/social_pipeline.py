from social_core.exceptions import AuthForbidden

from django.contrib.auth import get_user_model

User = get_user_model()


def create_user(strategy, details, backend, user=None, *args, **kwargs):
    if user:
        return {'is_new': False}

    email = details.get('email')
    if not email:
        raise AuthForbidden(backend, 'Email is required to create an account.')

    first_name = details.get('first_name', '')
    last_name = details.get('last_name', '')

    user = User.objects.create_user(
        email=email,
        password=None,
        first_name=first_name,
        last_name=last_name,
    )
    user.is_active = True
    user.save()
    return {'is_new': True, 'user': user}
