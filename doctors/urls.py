from django.urls import path
from users.views import ChangeEmailView, ChangePasswordView
from .views import DoctorMeProfileView, DoctorRateView, RescheduleDoctorSessionView, UpdateDoctorSummaryView, DoctorLandingPageView, DoctorSessionsView, ListDoctorsView, RequestDoctorView, CheckDoctorRequestView, ListDoctorRequestsView, ManageDoctorRequestView, DoctorPatientsView, ChatbotProfileListView, ImportantMessagesView, CreateDoctorSessionView

urlpatterns = [
    path('dashboard/', DoctorLandingPageView.as_view(), name='doctor-dashboard'),
    path("requests/", ListDoctorRequestsView.as_view(), name="doctor-requests"),
    path("manage-request/<int:pk>/", ManageDoctorRequestView.as_view(), name="manage-request"),
    path("sessions/", DoctorSessionsView.as_view(), name="doctor-sessions"),
    path("create-session/", CreateDoctorSessionView.as_view(), name="create-doctor-session"),
    path("reschedule-session/<int:session_id>/", RescheduleDoctorSessionView.as_view(), name="reschedule-session"),
    path("update-summary/<int:session_id>/", UpdateDoctorSummaryView.as_view(), name="update-doctor-summary"),
    path("list/", ListDoctorsView.as_view(), name="list-doctors"),
    path("request/<int:doctor_id>/", RequestDoctorView.as_view(), name="request-doctor"),
    path("check-request/<int:doctor_id>/", CheckDoctorRequestView.as_view(), name="check-doctor-request"),
    path("patients/", DoctorPatientsView.as_view(), name="doctor-patients"),
    path("chatbot-data/<int:patient_id>/", ChatbotProfileListView.as_view(), name="chatbot-profile"),
    path("chatbot-data/<int:patient_id>/important-messages/", ImportantMessagesView.as_view(), name="important-messages"),


    path('profile/', DoctorMeProfileView.as_view(), name='doctor-profile'),
    path('change-password/', ChangePasswordView.as_view(), name='doctor-change-password'),
    path("change-email/", ChangeEmailView.as_view(), name="doctor-change-email"),

    path("rate/<int:doctor_id>/", DoctorRateView.as_view(), name="doctor-rate"),
]
