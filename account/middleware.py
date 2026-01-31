# account/middleware.py
from django.shortcuts import redirect

from account.models import DispatcherProfile, Shop

class EnsureRoleMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            allowed_paths = [
                '/account/choose-role/',
                '/account/customer/setup/',
                '/account/shop/',
                '/account/dispatcher/',
                '/logout',
                '/account/activate',
            ]
            # if user missing role and not on onboarding routes, redirect
            if not getattr(request.user, 'role', None) or request.user.role == 'pending':
                path = request.path
                # allow static, admin, API and onboarding URLs through
                if not any(path.startswith(p) for p in allowed_paths) and not path.startswith('/admin'):
                    return redirect('choose_role')
            else:
                path = request.path
                if request.user.role == 'shop':
                    shop = Shop.objects.filter(owner=request.user).first()
                    if not shop or not shop.is_active:
                        if (
                            not path.startswith('/account/shop/')
                            and not path.startswith('/account/choose-role/')
                            and not path.startswith('/admin')
                            and not path.startswith('/static')
                            and not path.startswith('/media')
                        ):
                            return redirect('account:shop_info')
                if request.user.role == 'dispatcher':
                    profile = DispatcherProfile.objects.filter(user=request.user).first()
                    complete = bool(
                        profile
                        and profile.full_name
                        and profile.id_number
                        and profile.vehicle_type
                        and profile.plate_number
                    )
                    if not complete:
                        if (
                            not path.startswith('/account/dispatcher/')
                            and not path.startswith('/account/choose-role/')
                            and not path.startswith('/admin')
                            and not path.startswith('/static')
                            and not path.startswith('/media')
                        ):
                            return redirect('account:dispatcher_personal')
        return self.get_response(request)
