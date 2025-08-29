from django.urls import path
from .views import (
    GroupListView, GroupCreateView, GroupDeleteView,
    GroupQuestionListView, AnswerListView
)

urlpatterns = [
    path('groups/', GroupListView.as_view(), name='group-list'),
    path('groups/create/', GroupCreateView.as_view(), name='group-create'),
    path('groups/<int:pk>/delete/', GroupDeleteView.as_view(), name='group-delete'),
    path('groups/<int:group_id>/questions/', GroupQuestionListView.as_view(), name='group-questions'),
    path('questions/<int:question_id>/answers/', AnswerListView.as_view(), name='question-answers'),
]
