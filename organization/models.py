from django.db import models

# Create your models here.
from django.db import models
from django.conf import settings
# Create your models here.
class Organization(models.Model):
    name=models.CharField(max_length=255)
    location=models.CharField(max_length=255)
    details=models.JSONField(null=True)
    user=models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="organization_profile")