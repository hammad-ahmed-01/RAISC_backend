from django.urls import path
from users.views import ChangeEmailView, ChangePasswordView
from .views import (
    CurrentPsychologistView,
    DeleteDoctorSessionView,
    DoctorMeProfileView,
    DoctorRateView,
    LatestSessionView,
    PreviousSessionView,
    RescheduleDoctorSessionView,
    UpdateDoctorSummaryView,
    DoctorLandingPageView,
    DoctorSessionsView,
    ListDoctorsView,
    RequestDoctorView,
    CheckDoctorRequestView,
    DoctorPendingRequestsView,     # NEW (doctor sees pending)
    PatientRequestsView,           # NEW (patient sees all statuses)
    ManageDoctorRequestView,
    CancelDoctorRequestView,       # NEW (patient cancels)
    DoctorPatientsView,
    ChatbotProfileListView,
    ImportantMessagesView,
    CreateDoctorSessionView,
)

urlpatterns = [
    path('dashboard/', DoctorLandingPageView.as_view(), name='doctor-dashboard'),

    # doctor ⇄ patient requests
    path("requests/", DoctorPendingRequestsView.as_view(), name="doctor-requests"),               # doctor (pending only)
    path("patient/requests/", PatientRequestsView.as_view(), name="patient-requests"),            # patient (all)
    path("manage-request/<int:pk>/", ManageDoctorRequestView.as_view(), name="manage-request"),    # doctor PATCH approve/reject
    # patient create/check/cancel
    path("request/<int:doctor_id>/", RequestDoctorView.as_view(), name="request-doctor"),
    path("check-request/<int:doctor_id>/", CheckDoctorRequestView.as_view(), name="check-doctor-request"),
    path("request/<int:doctor_id>/cancel/", CancelDoctorRequestView.as_view(), name="cancel-doctor-request"),     # supports POST
    path("request/cancel/<int:doctor_id>/", CancelDoctorRequestView.as_view(), name="cancel-doctor-request-alt"), # supports POST
    # also support DELETE /request/<doctor_id>/
    # (handled in the same view)

    # sessions
    path("sessions/", DoctorSessionsView.as_view(), name="doctor-sessions"),
    path("create-session/", CreateDoctorSessionView.as_view(), name="create-doctor-session"),
    path("delete-session/<int:session_id>/", DeleteDoctorSessionView.as_view(), name="delete-session"),
    path("reschedule-session/<int:session_id>/", RescheduleDoctorSessionView.as_view(), name="reschedule-session"),
    path("update-summary/<int:session_id>/", UpdateDoctorSummaryView.as_view(), name="update-doctor-summary"),
    path("previous-session/", PreviousSessionView.as_view(), name="previous-session"),

    # doctor discovery
    path("list/", ListDoctorsView.as_view(), name="list-doctors"),

    # doctor’s patients & chatbot data
    path("patients/", DoctorPatientsView.as_view(), name="doctor-patients"),
    path("chatbot-data/<int:patient_id>/", ChatbotProfileListView.as_view(), name="chatbot-profile"),
    path("chatbot-data/<int:patient_id>/important-messages/", ImportantMessagesView.as_view(), name="important-messages"),

    # doctor profile & account
    path('profile/', DoctorMeProfileView.as_view(), name='doctor-profile'),
    path('change-password/', ChangePasswordView.as_view(), name='doctor-change-password'),
    path("change-email/", ChangeEmailView.as_view(), name="doctor-change-email"),

    # rating
    path("rate/<int:doctor_id>/", DoctorRateView.as_view(), name="doctor-rate"),

    # NEW integration points used by your Next.js app:
    path("psychologist/current/", CurrentPsychologistView.as_view(), name="psychologist-current"),
    path("latest-session/", LatestSessionView.as_view(), name="latest-session"),
]
