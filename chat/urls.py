from django.urls import path
from .views import ChatGroupListView, QuestionListCreateView, MessageListCreateView

urlpatterns = [
    path('groups/', ChatGroupListView.as_view(), name='chatgroup-list'),
    path('groups/<int:group_id>/questions/', QuestionListCreateView.as_view(), name='question-list-create'),
    path('questions/<int:question_id>/messages/', MessageListCreateView.as_view(), name='message-list-create'),
]
