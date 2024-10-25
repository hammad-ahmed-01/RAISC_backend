from django.db import models
from django.conf import settings

class ChatGroup(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class Question(models.Model):
    group = models.ForeignKey(ChatGroup, on_delete=models.CASCADE, related_name='questions')
    asked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='questions',
        limit_choices_to={'user_type': 'patient'}
    )
    session_id = models.CharField(max_length=255, null=True, blank=True)  # For unauthenticated users
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Question {self.id} by {self.asked_by}"

class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    answered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='answers',
        null=True,  # Allow null for unauthenticated users
        blank=True  # Allow blank for unauthenticated users
    )
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Answer {self.id} by {self.answered_by}"
