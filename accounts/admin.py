from django.contrib import admin
from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display  = ['user', 'phone', 'city', 'country', 'created_at']
    search_fields = ['user__username', 'user__email', 'city', 'country']
    list_filter   = ['country', 'created_at']
    readonly_fields = ['created_at', 'updated_at']
