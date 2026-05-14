from django.contrib import admin
from .models import CV, Education, Experience, Skill, Language, Interest


class EducationInline(admin.TabularInline):
    model = Education
    extra = 0


class ExperienceInline(admin.TabularInline):
    model = Experience
    extra = 0


class SkillInline(admin.TabularInline):
    model = Skill
    extra = 0


class LanguageInline(admin.TabularInline):
    model = Language
    extra = 0


class InterestInline(admin.TabularInline):
    model = Interest
    extra = 0


@admin.register(CV)
class CVAdmin(admin.ModelAdmin):
    list_display  = ['title', 'user', 'template', 'current_step', 'is_complete', 'updated_at']
    list_filter   = ['template', 'is_complete']
    search_fields = ['title', 'user__username', 'full_name']
    readonly_fields = ['created_at', 'updated_at']
    inlines       = [EducationInline, ExperienceInline, SkillInline, LanguageInline, InterestInline]


@admin.register(Education)
class EducationAdmin(admin.ModelAdmin):
    list_display  = ['institution', 'degree', 'cv', 'start_date', 'end_date', 'is_current']
    list_filter   = ['degree', 'is_current']
    search_fields = ['institution', 'cv__user__username']


@admin.register(Experience)
class ExperienceAdmin(admin.ModelAdmin):
    list_display  = ['position', 'company', 'cv', 'employment_type', 'start_date', 'is_current']
    list_filter   = ['employment_type', 'is_current']
    search_fields = ['position', 'company', 'cv__user__username']


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display  = ['name', 'category', 'proficiency', 'cv']
    list_filter   = ['category', 'proficiency']


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display  = ['name', 'level', 'cv']
    list_filter   = ['level']


@admin.register(Interest)
class InterestAdmin(admin.ModelAdmin):
    list_display  = ['name', 'cv']
