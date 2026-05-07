import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import CV, Education, Experience, Skill, Language, Interest
from .forms import (
    CVPersonalForm,
    EducationFormSet, ExperienceFormSet,
    SkillFormSet, LanguageFormSet, InterestFormSet,
)

STEP_TITLES = [
    'Personal Information',
    'Education',
    'Work Experience',
    'Skills & Languages',
    'Review',
]

STEP_LABELS = ['Personal', 'Education', 'Experience', 'Skills', 'Review']


@login_required
def cv_new(request):
    cv = CV.objects.create(user=request.user, title='My CV', current_step=1)
    return redirect('cv:step', pk=cv.pk, step=1)


@login_required
def cv_step(request, pk, step):
    cv   = get_object_or_404(CV, pk=pk, user=request.user)
    step = int(step)

    if step < 1 or step > 5:
        return redirect('cv:step', pk=cv.pk, step=1)

    context = {
        'cv':          cv,
        'step':        step,
        'step_title':  STEP_TITLES[step - 1],
        'step_labels': STEP_LABELS,
    }

    # ── Step 1: Personal Info ──
    if step == 1:
        if request.method == 'POST':
            form = CVPersonalForm(request.POST, request.FILES, instance=cv)
            if form.is_valid():
                cv = form.save(commit=False)
                cv.field_styles = form.cleaned_data.get('field_styles', {})
            else:
                # Save whatever fields we can directly — never block the user
                safe_fields = [
                    'title', 'template', 'full_name', 'job_title', 'email', 'phone',
                    'address', 'city', 'country', 'postal_code',
                    'linkedin', 'github', 'website',
                    'summary', 'primary_color', 'secondary_color',
                    'font_family', 'font_size',
                ]
                for field in safe_fields:
                    val = request.POST.get(field, '').strip()
                    if val:
                        setattr(cv, field, val)
                import json as _j
                raw_fs = request.POST.get('field_styles', '')
                try:
                    cv.field_styles = _j.loads(raw_fs) if raw_fs else {}
                except Exception:
                    cv.field_styles = {}
                if request.FILES.get('profile_photo'):
                    cv.profile_photo = request.FILES['profile_photo']

            cv.current_step = max(cv.current_step, 2)
            if 'save_exit' in request.POST:
                cv.save()
                messages.success(request, "Personal information saved.")
                return redirect('dashboard:index')
            cv.save()
            return redirect('cv:step', pk=cv.pk, step=2)
        else:
            form = CVPersonalForm(instance=cv)
        context['form'] = form
        return render(request, 'cv/step1_personal.html', context)

    # ── Step 2: Education ──
    elif step == 2:
        if request.method == 'POST':
            formset = EducationFormSet(request.POST, instance=cv, prefix='educations')
            if formset.is_valid():
                formset.save()
                cv.current_step = max(cv.current_step, 3)
                if 'save_exit' in request.POST:
                    cv.save()
                    messages.success(request, "Education saved.")
                    return redirect('dashboard:index')
                cv.save()
                return redirect('cv:step', pk=cv.pk, step=3)
            else:
                messages.error(request, "Please correct the errors below.")
        else:
            formset = EducationFormSet(instance=cv, prefix='educations')
        context['formset'] = formset
        return render(request, 'cv/step2_education.html', context)

    # ── Step 3: Experience ──
    elif step == 3:
        if request.method == 'POST':
            formset = ExperienceFormSet(request.POST, instance=cv, prefix='experiences')
            if formset.is_valid():
                formset.save()
                cv.current_step = max(cv.current_step, 4)
                if 'save_exit' in request.POST:
                    cv.save()
                    messages.success(request, "Work experience saved.")
                    return redirect('dashboard:index')
                cv.save()
                return redirect('cv:step', pk=cv.pk, step=4)
            else:
                messages.error(request, "Please correct the errors below.")
        else:
            formset = ExperienceFormSet(instance=cv, prefix='experiences')
        context['formset'] = formset
        return render(request, 'cv/step3_experience.html', context)

    # ── Step 4: Skills, Languages, Interests ──
    elif step == 4:
        if request.method == 'POST':
            skill_formset    = SkillFormSet(request.POST,    instance=cv, prefix='skills')
            language_formset = LanguageFormSet(request.POST, instance=cv, prefix='languages')
            interest_formset = InterestFormSet(request.POST, instance=cv, prefix='interests')

            all_valid = (
                skill_formset.is_valid() and
                language_formset.is_valid() and
                interest_formset.is_valid()
            )

            if all_valid:
                skill_formset.save()
                language_formset.save()
                interest_formset.save()
                cv.current_step = max(cv.current_step, 5)
                cv.is_complete  = True
                if 'save_exit' in request.POST:
                    cv.save()
                    messages.success(request, "Skills and languages saved.")
                    return redirect('dashboard:index')
                cv.save()
                return redirect('cv:step', pk=cv.pk, step=5)
            else:
                messages.error(request, "Please correct the errors below.")
        else:
            skill_formset    = SkillFormSet(instance=cv,    prefix='skills')
            language_formset = LanguageFormSet(instance=cv, prefix='languages')
            interest_formset = InterestFormSet(instance=cv, prefix='interests')

        context['skill_formset']    = skill_formset
        context['language_formset'] = language_formset
        context['interest_formset'] = interest_formset
        return render(request, 'cv/step4_skills.html', context)

    # ── Step 5: Review ──
    elif step == 5:
        context['experiences'] = cv.experiences.all()
        context['educations']  = cv.educations.all()
        context['skills']      = cv.skills.all()
        context['languages']   = cv.languages.all()
        context['interests']   = cv.interests.all()
        return render(request, 'cv/step5_review.html', context)


@login_required
def cv_delete(request, pk):
    cv = get_object_or_404(CV, pk=pk, user=request.user)
    if request.method == 'POST':
        title = cv.title
        cv.delete()
        messages.success(request, f"'{title}' has been deleted.")
    return redirect('dashboard:index')


@login_required
def cv_autosave(request, pk, step):
    """
    AJAX endpoint: silently save the current step's form data.
    Returns JSON {ok: true/false, errors: [...]}
    """
    import json as _json
    from django.http import JsonResponse
    from django.views.decorators.http import require_POST

    if request.method != 'POST':
        return JsonResponse({'ok': False, 'errors': ['Method not allowed']}, status=405)

    cv = get_object_or_404(CV, pk=pk, user=request.user)

    if step == 1:
        form = CVPersonalForm(request.POST, request.FILES, instance=cv)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.field_styles = form.cleaned_data.get('field_styles', {})
            obj.current_step = max(obj.current_step, 1)
            obj.save()
            return JsonResponse({'ok': True})
        return JsonResponse({'ok': False, 'errors': form.errors.get_json_data()})

    elif step == 2:
        formset = EducationFormSet(request.POST, instance=cv, prefix='educations')
        if formset.is_valid():
            formset.save()
            cv.save()
            return JsonResponse({'ok': True})
        return JsonResponse({'ok': False, 'errors': str(formset.errors)})

    elif step == 3:
        formset = ExperienceFormSet(request.POST, instance=cv, prefix='experiences')
        if formset.is_valid():
            formset.save()
            cv.save()
            return JsonResponse({'ok': True})
        return JsonResponse({'ok': False, 'errors': str(formset.errors)})

    elif step == 4:
        sf = SkillFormSet(request.POST,    instance=cv, prefix='skills')
        lf = LanguageFormSet(request.POST, instance=cv, prefix='languages')
        inf = InterestFormSet(request.POST, instance=cv, prefix='interests')
        if sf.is_valid() and lf.is_valid() and inf.is_valid():
            sf.save(); lf.save(); inf.save()
            cv.save()
            return JsonResponse({'ok': True})
        return JsonResponse({'ok': False, 'errors': str(sf.errors + lf.errors)})

    return JsonResponse({'ok': False, 'errors': ['Invalid step']})