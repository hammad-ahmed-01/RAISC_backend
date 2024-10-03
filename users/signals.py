from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, Profile
from rest_framework.authtoken.models import Token

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_or_update_user_profile(sender, instance=None, created=False, **kwargs):
    if created:
        Profile.objects.create(user=instance)
        Token.objects.create(user=instance)
    instance.profile.save()
