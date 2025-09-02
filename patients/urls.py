from django.urls import path
from users.views import ChangeEmailView, ChangePasswordView
from .views import PatientLandingPageView, CalendarListView, PatientMeProfileView, UserProfileView, PatientSessionsView, DoctorSummaryView

urlpatterns = [
    path('dashboard/', PatientLandingPageView.as_view(), name='patient-dashboard'),
    path("sessions/", PatientSessionsView.as_view(), name="patient-sessions"),
    path('data/<str:chatbot_session_id>/', UserProfileView.as_view(), name='user-data'),
    path("doctor-summary/<str:session_token>/", DoctorSummaryView.as_view(), name="doctor-summary"),


    path('profile/', PatientMeProfileView.as_view(), name='patient-profile'),
    path('change-password/', ChangePasswordView.as_view(), name='patient-change-password'),
    path("change-email/", ChangeEmailView.as_view(), name="patient-change-email"),
]
