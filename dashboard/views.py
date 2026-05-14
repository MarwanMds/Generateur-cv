from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from cv.models import CV


@login_required
def index(request):
    """Dashboard — list all CVs for the logged-in user."""
    cvs = CV.objects.filter(user=request.user).order_by('-updated_at')
    profile = request.user.profile

    # Most-used template across user's CVs
    template_counts = {}
    for cv in cvs:
        template_counts[cv.template] = template_counts.get(cv.template, 0) + 1
    fav_template = max(template_counts, key=template_counts.get) if template_counts else None

    context = {
        'cvs':          cvs,
        'cv_count':     cvs.count(),
        'complete':     cvs.filter(is_complete=True).count(),
        'drafts':       cvs.filter(is_complete=False).count(),
        'profile':      profile,
        'fav_template': fav_template,
    }
    return render(request, 'dashboard/dashboard.html', context)
