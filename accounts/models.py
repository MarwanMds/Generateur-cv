from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    """
    Extends the built-in Django User with extra fields.
    Created automatically when a new User is registered (via signal).
    """
    user         = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone        = models.CharField(max_length=20, blank=True)
    address      = models.CharField(max_length=255, blank=True)
    city         = models.CharField(max_length=100, blank=True)
    country      = models.CharField(max_length=100, blank=True)
    headline     = models.CharField(max_length=120, blank=True, help_text="e.g. Full Stack Developer")
    bio          = models.TextField(blank=True)
    avatar       = models.ImageField(upload_to='avatars/', blank=True, null=True)
    linkedin_url = models.URLField(blank=True)
    github_url   = models.URLField(blank=True)
    website_url  = models.URLField(blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile of {self.user.username}"

    def get_full_name(self):
        return f"{self.user.first_name} {self.user.last_name}".strip() or self.user.username
