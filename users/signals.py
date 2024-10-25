from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User
from rest_framework.authtoken.models import Token

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        # Create authentication token for the user
        Token.objects.create(user=instance)
