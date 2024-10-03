# chat/models.py

from django.db import models
from django.conf import settings

class ChatGroup(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    # Add any other fields as necessary

    def __str__(self):
        return self.name

class Question(models.Model):
    group = models.ForeignKey(ChatGroup, on_delete=models.CASCADE, related_name='questions')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Question by {self.user.username if self.user else 'Anonymous'} in {self.group.name}"

class Message(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='messages')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def sender_role(self):
        return self.user.user_type if self.user else 'Anonymous'

    def __str__(self):
        return f"Message by {self.user.username if self.user else 'Anonymous'}"
