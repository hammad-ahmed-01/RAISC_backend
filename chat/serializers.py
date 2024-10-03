from rest_framework import serializers
from .models import Message, Question, ChatGroup
from users.serializers import UserSerializer

class MessageSerializer(serializers.ModelSerializer):
    sender_role = serializers.CharField(source='sender_role', read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'question', 'user', 'content', 'timestamp', 'sender_role']
        read_only_fields = ['user', 'timestamp', 'sender_role']


class QuestionSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ['id', 'group', 'user', 'content', 'timestamp', 'messages']
        read_only_fields = ['user', 'timestamp', 'messages']

class ChatGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatGroup
        fields = ['id', 'name', 'description']
