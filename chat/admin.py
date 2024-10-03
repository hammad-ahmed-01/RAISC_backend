from django.contrib import admin
from .models import ChatGroup, Question, Message

admin.site.register(ChatGroup)
admin.site.register(Question)
admin.site.register(Message)
