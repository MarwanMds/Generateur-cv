from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps


def admin_required(view_func):
    """Restricts access to staff users only."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not request.user.is_staff:
            messages.error(request, "You don't have permission to access the admin panel.")
            return redirect('dashboard:index')
        return view_func(request, *args, **kwargs)
    return wrapper
