from django.urls import path
from .views import UserRegistrationView, LoginView, UserDetailView

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='user-register'),
    path('login/', LoginView.as_view(), name='user-login'),
    path('me/', UserDetailView.as_view(), name='user-detail'),
]
