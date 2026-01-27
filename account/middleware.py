# account/middleware.py
from django.shortcuts import redirect

class EnsureRoleMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            allowed_paths = [
                '/account/choose-role/',
                '/account/shop/info/',
                '/account/dispatcher/personal/',
                '/account/customer/setup/',
                '/logout',
                '/account/activate',
            ]
            # if user missing role and not on onboarding routes, redirect
            if not getattr(request.user, 'role', None):
                path = request.path
                # allow static, admin, API and onboarding URLs through
                if not any(path.startswith(p) for p in allowed_paths) and not path.startswith('/admin'):
                    return redirect('account:choose_role')
        return self.get_response(request)
