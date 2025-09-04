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


# NEW: per-patient rating for a Doctor
class DoctorRating(models.Model):
    """
    Store each patient's rating for a specific Doctor (1..5), then aggregate.
    We link to the Doctor row (not just the User) because your frontend uses Doctor.id.
    """
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name="ratings")
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="doctor_ratings",
        limit_choices_to={'user_type': 'patient'}
    )
    stars = models.PositiveSmallIntegerField()  # 1..5
    comment = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (("doctor", "patient"),)
        indexes = [models.Index(fields=["doctor", "patient"])]

    def __str__(self):
        return f"Rating {self.stars} by patient {self.patient_id} for doctor {self.doctor_id}"
