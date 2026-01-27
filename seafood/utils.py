from account.models import Profile
from django.contrib.auth.models import User


def create_profile(strategy, details, response, user, *args, **kwargs):

    if Profile.objects.filter(user=user).exists():
        pass
    else:
        new_profile = Profile(user=user)
        new_profile.save()
    return kwargs