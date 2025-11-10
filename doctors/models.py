from django.db import models
from django.conf import settings


class Doctor(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='doctor_profile'
    )
    professional_information = models.JSONField(default=dict)  # stores rating average too
    chatgroup_nickname = models.CharField(max_length=255, blank=True, null=True)
    rates = models.DecimalField(max_digits=7, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return self.user.username
    organization=models.ForeignKey(settings.AUTH_USER_MODEL,null=True, on_delete=models.CASCADE,limit_choices_to={'user_type': 'organization'}, related_name='employed_doctors')



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


class DoctorRating(models.Model):
    """
    One row per patient per Doctor (1..5 stars).
    IMPORTANT: This links to the Doctor row (not directly to AUTH_USER).
    """
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name="ratings")
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="doctor_ratings",
        limit_choices_to={'user_type': 'patient'}
    )
    stars = models.PositiveSmallIntegerField()  # integer 1..5
    comment = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (("doctor", "patient"),)
        indexes = [models.Index(fields=["doctor", "patient"])]

    def __str__(self):
        return f"Rating {self.stars} by patient {self.patient_id} for doctor {self.doctor_id}"
