from django import forms
from django.forms import inlineformset_factory
from .models import CV, Education, Experience, Skill, Language, Interest
import json


class FlexibleURLField(forms.CharField):
    """
    Accepts any string as a URL (no scheme/format enforcement).
    Lets users enter partial URLs like 'linkedin.com/in/name'
    without a server-side validation error.
    """
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('required', False)
        super().__init__(*args, **kwargs)

    def clean(self, value):
        value = super().clean(value)
        return value or ''


class FieldStylesField(forms.CharField):
    """
    Handles the hidden JSON input for per-field typography settings.
    Empty string → {} so the JSONField never receives invalid JSON.
    """
    widget = forms.HiddenInput

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('required', False)
        super().__init__(*args, **kwargs)

    def clean(self, value):
        value = (value or '').strip()
        if not value:
            return {}
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except (ValueError, TypeError):
            return {}

    def prepare_value(self, value):
        if isinstance(value, dict):
            return json.dumps(value)
        return value or '{}'


class CVPersonalForm(forms.ModelForm):

    # Plain CharField so partial/missing https:// never causes a validation error
    linkedin = FlexibleURLField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://linkedin.com/in/...'
        })
    )
    github = FlexibleURLField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://github.com/...'
        })
    )
    website = FlexibleURLField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://yoursite.com'
        })
    )

    # Accepts empty string from hidden input; always returns a valid dict
    field_styles = FieldStylesField()

    class Meta:
        model  = CV
        fields = [
            'title', 'template',
            'full_name', 'job_title', 'email', 'phone',
            'address', 'city', 'country', 'postal_code',
            'linkedin', 'github', 'website',
            'summary', 'profile_photo',
            'primary_color', 'secondary_color',
            'font_family', 'font_size',
            'field_styles',
        ]
        widgets = {
            'title':           forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. My Software Engineer CV'}),
            'template':        forms.Select(attrs={'class': 'form-select', 'id': 'id_template'}),
            'full_name':       forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'John Doe'}),
            'job_title':       forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Full Stack Developer'}),
            'email':           forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'john@example.com'}),
            'phone':           forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+212 6XX XX XX XX'}),
            'address':         forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Street address'}),
            'city':            forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Casablanca'}),
            'country':         forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Morocco'}),
            'postal_code':     forms.TextInput(attrs={'class': 'form-control', 'placeholder': '20000'}),
            'summary':         forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'A short professional summary...'}),
            'profile_photo':   forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'primary_color':   forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color', 'id': 'id_primary_color'}),
            'secondary_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color', 'id': 'id_secondary_color'}),
            'font_family':     forms.Select(attrs={'class': 'form-select', 'id': 'id_font_family'}),
            'font_size':       forms.Select(attrs={'class': 'form-select', 'id': 'id_font_size'}),
        }


class EducationForm(forms.ModelForm):
    class Meta:
        model  = Education
        fields = ['degree', 'field_of_study', 'institution', 'institution_location',
                  'start_date', 'end_date', 'is_current', 'grade', 'description']
        widgets = {
            'degree':               forms.Select(attrs={'class': 'form-select'}),
            'field_of_study':       forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Computer Science'}),
            'institution':          forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'University name'}),
            'institution_location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City, Country'}),
            'start_date':           forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date':             forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_current':           forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'description':          forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

EducationFormSet = inlineformset_factory(CV, Education, form=EducationForm, extra=1, can_delete=True)


class ExperienceForm(forms.ModelForm):
    class Meta:
        model  = Experience
        fields = ['position', 'company', 'company_location', 'employment_type',
                  'start_date', 'end_date', 'is_current', 'description']
        widgets = {
            'position':         forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Software Engineer'}),
            'company':          forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Company name'}),
            'company_location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City, Country'}),
            'employment_type':  forms.Select(attrs={'class': 'form-select'}),
            'start_date':       forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date':         forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_current':       forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'description':      forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

ExperienceFormSet = inlineformset_factory(CV, Experience, form=ExperienceForm, extra=1, can_delete=True)


class SkillForm(forms.ModelForm):
    class Meta:
        model  = Skill
        fields = ['name', 'category', 'proficiency']
        widgets = {
            'name':        forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Python'}),
            'category':    forms.Select(attrs={'class': 'form-select'}),
            'proficiency': forms.Select(attrs={'class': 'form-select'}),
        }

SkillFormSet = inlineformset_factory(CV, Skill, form=SkillForm, extra=1, can_delete=True)


class LanguageForm(forms.ModelForm):
    class Meta:
        model  = Language
        fields = ['name', 'level']
        widgets = {
            'name':  forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. English'}),
            'level': forms.Select(attrs={'class': 'form-select'}),
        }

LanguageFormSet = inlineformset_factory(CV, Language, form=LanguageForm, extra=1, can_delete=True)


class InterestForm(forms.ModelForm):
    class Meta:
        model  = Interest
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Photography', 'style': 'width:160px'}),
        }

InterestFormSet = inlineformset_factory(CV, Interest, form=InterestForm, extra=1, can_delete=True)