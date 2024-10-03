from django.db import models
from users.models import User

class Appointment(models.Model):
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='patient_appointments')
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='doctor_appointments')
    date_time = models.DateTimeField()
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Appointment between {self.patient.username} and {self.doctor.username} on {self.date_time}"
