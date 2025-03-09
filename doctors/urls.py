from django.urls import path
from .views import DoctorLandingPageView, DoctorSessionsView, ListDoctorsView, RequestDoctorView, CheckDoctorRequestView, ListDoctorRequestsView, ManageDoctorRequestView, DoctorPatientsView, ChatbotProfileListView, ImportantMessagesView
urlpatterns = [
    path('dashboard/', DoctorLandingPageView.as_view(), name='doctor-dashboard'),
    path("requests/", ListDoctorRequestsView.as_view(), name="doctor-requests"),
    path("manage-request/<int:pk>/", ManageDoctorRequestView.as_view(), name="manage-request"),
    path("sessions/", DoctorSessionsView.as_view(), name="doctor-sessions"),
    path("list/", ListDoctorsView.as_view(), name="list-doctors"),
    path("request/<int:doctor_id>/", RequestDoctorView.as_view(), name="request-doctor"),
    path("check-request/<int:doctor_id>/", CheckDoctorRequestView.as_view(), name="check-doctor-request"),
    path("patients/", DoctorPatientsView.as_view(), name="doctor-patients"),
    path("chatbot-data/<int:patient_id>/", ChatbotProfileListView.as_view(), name="chatbot-profile"),
    path("chatbot-data/<int:patient_id>/important-messages/", ImportantMessagesView.as_view(), name="important-messages"),
]
