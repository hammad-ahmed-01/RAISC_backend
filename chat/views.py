from rest_framework import generics, permissions
from .models import ChatGroup
from .serializers import ChatGroupSerializer
from .models import Question
from .serializers import QuestionSerializer
from .models import Message
from .serializers import MessageSerializer
from users.permissions import IsPatientOrReadOnly
class ChatGroupListView(generics.ListAPIView):
    queryset = ChatGroup.objects.all()
    serializer_class = ChatGroupSerializer
    permission_classes = [permissions.IsAuthenticated]


class QuestionListCreateView(generics.ListCreateAPIView):
    serializer_class = QuestionSerializer
    permission_classes = [IsPatientOrReadOnly]

    def get_queryset(self):
        group_id = self.kwargs.get('group_id')
        return Question.objects.filter(group_id=group_id)

    def perform_create(self, serializer):
        group_id = self.kwargs.get('group_id')
        serializer.save(user=self.request.user, group_id=group_id)


class MessageListCreateView(generics.ListCreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        question_id = self.kwargs.get('question_id')
        return Message.objects.filter(question_id=question_id)

    def perform_create(self, serializer):
        question_id = self.kwargs.get('question_id')
        serializer.save(user=self.request.user, question_id=question_id)
