from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings

class User(AbstractUser):
    USER_TYPES = (
        ('staff', 'Staff'),
        ('patient', 'Patient'),
        ('doctor', 'Doctor'),
        ('organization', 'Organization')
    )
    user_type = models.CharField(max_length=12, choices=USER_TYPES)

    def __str__(self):
        return f"{self.username} ({self.user_type})"

class Calendar(models.Model):
    title = models.CharField(max_length=255, blank=True, null=True)
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='patient_calendars',
        limit_choices_to={'user_type': 'patient'}
    )
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='doctor_calendars',
        limit_choices_to={'user_type': 'doctor'}
    )
    date = models.DateField(null=True)  # Added Date Field
    details = models.JSONField(default=dict)
    description = models.CharField(max_length=255, blank=True, null=True)
    doctor_summary = models.CharField(max_length=255, blank=True, null=True)
    patient_update = models.JSONField(default=dict, blank=True, null=True)

    def __str__(self):
        return f"{self.title}"
