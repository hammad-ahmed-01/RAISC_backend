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


class DoctorRequest(models.Model):
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="doctor_requests",
        limit_choices_to={'user_type': 'patient'}
    )
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="requested_by_patients",
        limit_choices_to={'user_type': 'doctor'}
    )
    status = models.CharField(
        max_length=20,
        choices=[("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected")],
        default="pending"
    )
    requested_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.patient.username} requested {self.doctor.username}"
