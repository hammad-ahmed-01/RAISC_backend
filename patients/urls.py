from django.urls import path
from .views import PatientLandingPageView, CalendarListView, UserProfileView, PatientSessionsView

urlpatterns = [
    path('dashboard/', PatientLandingPageView.as_view(), name='patient-dashboard'),
    path("sessions/", PatientSessionsView.as_view(), name="patient-sessions"),
    path('data/<str:chatbot_session_id>/', UserProfileView.as_view(), name='user-data'),
]
