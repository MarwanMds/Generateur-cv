from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Count, Q
from cv.models import CV
from accounts.models import Profile
from .decorators import admin_required


# ── Dashboard Overview ────────────────────────────────────

@admin_required
def overview(request):
    """Admin panel home — stats overview."""
    total_users    = User.objects.filter(is_staff=False).count()
    total_cvs      = CV.objects.count()
    complete_cvs   = CV.objects.filter(is_complete=True).count()
    recent_users   = User.objects.filter(is_staff=False).order_by('-date_joined')[:5]
    recent_cvs     = CV.objects.order_by('-created_at')[:5]

    context = {
        'total_users':  total_users,
        'total_cvs':    total_cvs,
        'complete_cvs': complete_cvs,
        'recent_users': recent_users,
        'recent_cvs':   recent_cvs,
    }
    return render(request, 'admin_panel/overview.html', context)


# ── Users Management ──────────────────────────────────────

@admin_required
def users_list(request):
    """List all non-staff users with their CV counts."""
    search = request.GET.get('q', '')
    users = User.objects.filter(is_staff=False).annotate(
        cv_count=Count('cvs')
    ).order_by('-date_joined')

    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )

    context = {'users': users, 'search': search}
    return render(request, 'admin_panel/users_list.html', context)


@admin_required
def user_detail(request, user_id):
    """View a specific user's profile and CVs."""
    target_user = get_object_or_404(User, pk=user_id, is_staff=False)
    cvs = CV.objects.filter(user=target_user).order_by('-updated_at')
    context = {'target_user': target_user, 'cvs': cvs}
    return render(request, 'admin_panel/user_detail.html', context)


@admin_required
def user_delete(request, user_id):
    """Delete a user and all their data."""
    target_user = get_object_or_404(User, pk=user_id, is_staff=False)
    if request.method == 'POST':
        username = target_user.username
        target_user.delete()
        messages.success(request, f"User '{username}' and all their data have been deleted.")
        return redirect('admin_panel:users_list')
    return render(request, 'admin_panel/user_confirm_delete.html', {'target_user': target_user})


@admin_required
def user_toggle_staff(request, user_id):
    """Promote or demote a user to/from staff."""
    target_user = get_object_or_404(User, pk=user_id)
    if request.method == 'POST':
        target_user.is_staff = not target_user.is_staff
        target_user.save()
        status = "promoted to admin" if target_user.is_staff else "demoted to regular user"
        messages.success(request, f"User '{target_user.username}' has been {status}.")
    return redirect('admin_panel:users_list')


# ── CVs Management ────────────────────────────────────────

@admin_required
def cvs_list(request):
    """List all CVs across all users."""
    search = request.GET.get('q', '')
    cvs = CV.objects.select_related('user').order_by('-updated_at')

    if search:
        cvs = cvs.filter(
            Q(title__icontains=search) |
            Q(full_name__icontains=search) |
            Q(user__username__icontains=search)
        )

    context = {'cvs': cvs, 'search': search}
    return render(request, 'admin_panel/cvs_list.html', context)



@admin_required
def cv_preview(request, cv_id):
    """Preview any user's CV — bypasses ownership check."""
    cv = get_object_or_404(CV, pk=cv_id)
    context = {
        'cv':          cv,
        'step':        5,
        'step_title':  'Review',
        'step_labels': ['Personal', 'Education', 'Experience', 'Skills', 'Review'],
        'experiences': cv.experiences.all(),
        'educations':  cv.educations.all(),
        'skills':      cv.skills.all(),
        'languages':   cv.languages.all(),
        'interests':   cv.interests.all(),
        'is_admin_preview': True,
    }
    return render(request, 'cv/step5_review.html', context)

@admin_required
def cv_delete(request, cv_id):
    """Delete any CV."""
    cv = get_object_or_404(CV, pk=cv_id)
    if request.method == 'POST':
        title = cv.title
        owner = cv.user.username
        cv.delete()
        messages.success(request, f"CV '{title}' by '{owner}' has been deleted.")
        return redirect('admin_panel:cvs_list')
    return render(request, 'admin_panel/cv_confirm_delete.html', {'cv': cv})