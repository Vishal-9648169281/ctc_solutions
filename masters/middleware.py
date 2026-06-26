from django.shortcuts import redirect
from django.contrib import messages

class RoleMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

def get_user_role(user):
    try:
        return user.profile.role
    except:
        return 'admin' if user.is_superuser else 'sales'

def role_required(*roles):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            user_role = get_user_role(request.user)
            if request.user.is_superuser or user_role in roles:
                return view_func(request, *args, **kwargs)
            messages.error(request, 'Access Denied! You do not have permission.')
            return redirect('dashboard')
        return wrapper
    return decorator
