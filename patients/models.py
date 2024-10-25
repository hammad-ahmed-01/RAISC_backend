from django.db import models
from django.conf import settings

class PatientProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='patient_profile'
    )
    level = models.IntegerField(default=0)
    associated_psychologist = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='patients',
        limit_choices_to={'user_type': 'doctor'}
    )
    profile_data = models.JSONField(default=dict)

    def __str__(self):
        return self.user.username
