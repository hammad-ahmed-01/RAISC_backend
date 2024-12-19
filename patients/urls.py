from django.urls import path
from .views import PatientLandingPageView, CalendarListView, UserProfileView

urlpatterns = [
    path('dashboard/', PatientLandingPageView.as_view(), name='patient-dashboard'),
    path('calendar/', CalendarListView.as_view(), name='calendar-list'),
    path('data/<str:chatbot_session_id>/', UserProfileView.as_view(), name='user-data'),
]
