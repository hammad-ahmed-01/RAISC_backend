from rest_framework import generics, permissions
from .models import ChatGroup, Question, Answer
from .serializers import QuestionSerializer, AnswerSerializer, ChatGroupSerializer
from .permissions import CanAskQuestion, CanAnswerQuestion, CanDeleteQuestionOrAnswer

class QuestionListCreateView(generics.ListCreateAPIView):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    permission_classes = [CanAskQuestion]

    def perform_create(self, serializer):
        if self.request.user.is_authenticated:
            serializer.save(asked_by=self.request.user)
        else:
            serializer.save(asked_by=None)  # Anonymous user

class AnswerCreateView(generics.CreateAPIView):
    queryset = Answer.objects.all()
    serializer_class = AnswerSerializer
    permission_classes = [CanAnswerQuestion]

    def perform_create(self, serializer):
        serializer.save(answered_by=self.request.user)

class GroupListView(generics.ListAPIView):
    queryset = ChatGroup.objects.all()
    serializer_class = ChatGroupSerializer

class GroupCreateView(generics.CreateAPIView):
    queryset = ChatGroup.objects.all()
    serializer_class = ChatGroupSerializer
    permission_classes = [CanDeleteQuestionOrAnswer]  # Only staff can create

class GroupDeleteView(generics.DestroyAPIView):
    queryset = ChatGroup.objects.all()
    permission_classes = [CanDeleteQuestionOrAnswer]  # Only staff can delete

class GroupQuestionListView(generics.ListAPIView):
    serializer_class = QuestionSerializer

    def get_queryset(self):
        group_id = self.kwargs['group_id']
        return Question.objects.filter(group__id=group_id)

class AnswerListView(generics.ListAPIView):
    serializer_class = AnswerSerializer

    def get_queryset(self):
        question_id = self.kwargs['question_id']
        return Answer.objects.filter(question__id=question_id)
