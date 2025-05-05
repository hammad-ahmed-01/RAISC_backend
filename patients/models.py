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

class ChatbotProfile(models.Model):
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chatbot_profiles',
        limit_choices_to={'user_type': 'patient'}
    )
    collected_data = models.TextField()  # Stores extracted chatbot insights
    session_summary = models.TextField()  # AI-generated summary
    session_start_msg = models.IntegerField(default=0)
    session_end_msg = models.IntegerField(default=0)
    important_messages = models.TextField(null=True, blank=True)  # Highlighted messages
    date = models.DateTimeField(auto_now_add=True)  # Change to DateTimeField for accurate timestamp

    def __str__(self):
        return f"Chatbot Profile - {self.patient.username} ({self.date.strftime('%Y-%m-%d %H:%M:%S')})"


