from django.shortcuts import render, redirect


def home(request):
    """
    Public home page.
    Authenticated users are redirected directly to their dashboard.
    """
    if request.user.is_authenticated:
        return redirect('dashboard:index')
    return render(request, 'core/home.html')
