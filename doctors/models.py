from django.db import models
from django.conf import settings

class Doctor(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='doctor_profile'
    )
    professional_information = models.JSONField(default=dict)
    chatgroup_nickname = models.CharField(max_length=255, blank=True, null=True)
    rates = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return self.user.username
