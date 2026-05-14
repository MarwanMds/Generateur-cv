from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Profile


@receiver(post_save, sender=User)
def create_or_save_profile(sender, instance, created, **kwargs):
    """
    Create a Profile when a new User is registered.
    For existing users, get_or_create ensures no crash if profile is missing.
    """
    if created:
        Profile.objects.create(user=instance)
    else:
        # get_or_create handles old users who have no profile yet
        Profile.objects.get_or_create(user=instance)
        instance.profile.save()