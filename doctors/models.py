from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver


class Doctor(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='doctor_profile'
    )
    professional_information = models.JSONField(default=dict)  # keeps {"rating": float, "ratings_count": int}
    chatgroup_nickname = models.CharField(max_length=255, blank=True, null=True)
    rates = models.DecimalField(max_digits=7, decimal_places=2, blank=True, null=True)

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


class DoctorRating(models.Model):
    """
    One row per patient per Doctor.
    """
    doctor = models.ForeignKey('Doctor', on_delete=models.CASCADE, related_name="ratings")
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="doctor_ratings",
        limit_choices_to={'user_type': 'patient'}
    )
    stars = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "doctors_doctorrating"
        unique_together = (("doctor", "patient"),)
        indexes = [models.Index(fields=["doctor", "patient"])]

    def __str__(self):
        return f"Rating {self.stars} by patient {self.patient_id} for doctor {self.doctor_id}"


# -----------------------------
# Incremental average handling
# -----------------------------

def _get_pi(doctor: Doctor):
    """Return (avg, count, pi_dict) with safe defaults."""
    pi = dict(doctor.professional_information or {})
    avg = float(pi.get("rating") or 0.0)
    cnt = int(pi.get("ratings_count") or 0)
    return avg, cnt, pi

def _persist_pi(doctor: Doctor, avg: float, cnt: int):
    pi = dict(doctor.professional_information or {})
    pi["rating"] = round(float(avg), 1) if cnt > 0 else 0.0
    pi["ratings_count"] = int(cnt)
    doctor.professional_information = pi
    doctor.save(update_fields=["professional_information"])


@receiver(pre_save, sender=DoctorRating)
def _stash_old_stars(sender, instance: DoctorRating, **kwargs):
    """
    When updating an existing rating, fetch its current 'stars' so we can adjust the average.
    Stored on the instance as _old_stars (None for creates).
    """
    if instance.pk:
        try:
            instance._old_stars = sender.objects.only("stars").get(pk=instance.pk).stars  # type: ignore[attr-defined]
        except sender.DoesNotExist:
            instance._old_stars = None  # type: ignore[attr-defined]
    else:
        instance._old_stars = None  # type: ignore[attr-defined]


@receiver(post_save, sender=DoctorRating)
def _apply_average_on_save(sender, instance: DoctorRating, created, **kwargs):
    """
    Incrementally update the doctor's average & count.

    If created:
        new_avg = (old_avg * n + stars) / (n + 1), n = n + 1
    If updated (same patient changes rating):
        new_avg = (old_avg * n - old_stars + new_stars) / n
    """
    doctor = instance.doctor
    old_avg, n, _ = _get_pi(doctor)

    # Ensure 'n' is sane
    if n < 0:
        n = 0
        old_avg = 0.0

    if created or getattr(instance, "_old_stars", None) is None:
        # Treat as create
        new_n = n + 1
        new_avg = ((old_avg * n) + instance.stars) / new_n
        _persist_pi(doctor, new_avg, new_n)
    else:
        # Update existing rating
        old_stars = int(getattr(instance, "_old_stars", instance.stars))
        new_stars = int(instance.stars)
        # When n == 0 (shouldn't happen with an update), reset gracefully
        if n <= 0:
            _persist_pi(doctor, new_stars, 1)
        else:
            new_avg = ((old_avg * n) - old_stars + new_stars) / n
            _persist_pi(doctor, new_avg, n)


@receiver(post_delete, sender=DoctorRating)
def _apply_average_on_delete(sender, instance: DoctorRating, **kwargs):
    """
    Decrementally update the average when a rating is removed:
        if n > 1: new_avg = ((old_avg * n) - stars) / (n - 1), new_n = n - 1
        if n <= 1: reset to 0
    """
    doctor = instance.doctor
    old_avg, n, _ = _get_pi(doctor)

    if n <= 1:
        _persist_pi(doctor, 0.0, 0)
    else:
        new_n = n - 1
        new_avg = ((old_avg * n) - instance.stars) / new_n
        _persist_pi(doctor, new_avg, new_n)
