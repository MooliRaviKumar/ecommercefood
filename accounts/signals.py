# accounts/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, Profile

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        # Create profile when a new user is created
        Profile.objects.create(user=instance)
    else:
        # Save the profile if the user is updated
        try:
            instance.profile.save()
        except Profile.DoesNotExist:
            # In case profile is missing, create it
            Profile.objects.create(user=instance)
