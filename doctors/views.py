from django.shortcuts import get_object_or_404
from rest_framework import permissions, generics, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.filters import OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Avg, Count
from rest_framework.permissions import IsAuthenticated as DRFIsAuthenticated

from users.models import User, Calendar
from patients.models import PatientProfile, ChatbotProfile
from .models import Doctor, DoctorRequest, DoctorRating

from .serializers import (
    CurrentPsychologistSerializer,
    DoctorProfileSerializer,
    CalendarDoctorSerializer,
    DoctorRequestSerializer,
    DoctorRequestPostSerializer,
    DoctorViewPatientSerializer,
    ChatbotProfileSerializer,
    DoctorRatingSerializer,
    LatestSessionSerializer,  # NEW
)

# -------------------------
# Doctor dashboard landing
# -------------------------

class DoctorLandingPageView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        doctor_profile = getattr(request.user, "doctor_profile", None)
        if not doctor_profile:
            return Response({"error": "Doctor profile not found."}, status=status.HTTP_404_NOT_FOUND)

        profile_data = DoctorProfileSerializer(doctor_profile).data
        user_data = {
            "id": request.user.id,
            "username": request.user.username,
            "email": request.user.email,
            "user_type": getattr(request.user, "user_type", ""),
        }

        return Response(
            {
                "user": user_data,
                "doctor_profile": profile_data,
                "message": "Welcome to your doctor dashboard.",
            }
        )

# -------------------------
# Doctor's calendar entries
# -------------------------

class DoctorSessionsView(generics.ListAPIView):
    serializer_class = CalendarDoctorSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Calendar.objects.filter(doctor=self.request.user).order_by("-date")


class CreateDoctorSessionView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        data = request.data
        patient_id = data.get("patient_id")
        title = (data.get("title") or "").strip()
        description = (data.get("description") or "").strip()
        date = data.get("date")

        if not (patient_id and title and date):
            return Response({"error": "Missing required fields."}, status=status.HTTP_400_BAD_REQUEST)

        patient = get_object_or_404(User, id=patient_id)
        session = Calendar.objects.create(
            doctor=request.user,
            patient=patient,
            title=title,
            description=description,
            date=date,
        )
        return Response({"message": "Session created successfully.", "session_id": session.id}, status=status.HTTP_201_CREATED)


# -------------------------
# Public doctor listing API
# -------------------------

class ListDoctorsView(generics.ListAPIView):
    """
    GET /users/doctor/list/   (Token required)
    - Returns plain list (no pagination wrapper)
    - Matches Next.js route normalization
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    queryset = Doctor.objects.select_related("user").order_by("user__username")
    serializer_class = DoctorProfileSerializer
    pagination_class = None

# -------------------------
# Patient ↔ Doctor requests (UPDATED)
# -------------------------

class RequestDoctorView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, doctor_id):
        patient = request.user
        if getattr(patient, "user_type", "") != "patient":
            return Response({"error": "Only patients can request a doctor."}, status=403)

        # doctor_id is Doctor.pk -> resolve to User
        doc_obj = get_object_or_404(Doctor, id=doctor_id)
        doctor_user = doc_obj.user

        # Block duplicates if there's already an active request
        if DoctorRequest.objects.filter(
            patient=patient,
            doctor=doctor_user,
            status__in=["pending", "approved"],  # matches your current choices
        ).exists():
            return Response({"error": "You have already requested this doctor."}, status=400)

        dr = DoctorRequest.objects.create(patient=patient, doctor=doctor_user, status="pending")
        from .serializers import DoctorRequestPostSerializer
        return Response(DoctorRequestPostSerializer(dr).data, status=201)


class CheckDoctorRequestView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, doctor_id):
        patient = request.user
        if getattr(patient, "user_type", "") != "patient":
            return Response({"error": "Only patients can check requests."}, status=403)

        # doctor_id is Doctor.pk -> resolve to User
        doc_obj = get_object_or_404(Doctor, id=doctor_id)
        doctor_user = doc_obj.user

        exists = DoctorRequest.objects.filter(patient=patient, doctor=doctor_user).exists()
        return Response({"requested": exists}, status=200)

class ListDoctorRequestsView(generics.ListAPIView):
    """
    GET /users/doctor/requests/
    Lists PENDING requests for the authenticated doctor (User).
    """
    serializer_class = DoctorRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # doctor is a User on the DoctorRequest model in your code
        return (DoctorRequest.objects
                .filter(doctor=self.request.user, status="pending")
                .order_by("-requested_at"))


class ManageDoctorRequestView(generics.UpdateAPIView):
    """
    PATCH /users/doctor/manage-request/<pk>/
    Body: { "status": "accepted" | "request_again" }
    - accepted -> associate patient with this doctor (User)
    - request_again -> no association, just flip status
    """
    serializer_class = DoctorRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return DoctorRequest.objects.filter(doctor=self.request.user)

    def patch(self, request, *args, **kwargs):
        doctor_request = self.get_object()
        new_status = (request.data.get("status") or "").lower()

        if new_status not in {"accepted", "request_again"}:
            return Response({"error": "Invalid status. Use 'accepted' or 'request_again'."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Apply status change
        doctor_request.status = new_status
        doctor_request.save(update_fields=["status"])

        if new_status == "accepted":
            # Associate patient with this doctor (User)
            try:
                pp = PatientProfile.objects.get(user=doctor_request.patient)
            except PatientProfile.DoesNotExist:
                return Response({"error": "Patient profile not found."},
                                status=status.HTTP_404_NOT_FOUND)

            pp.associated_psychologist = doctor_request.doctor  # doctor is a User in your code
            # Optional: bump level if you want
            pp.level = max(2, pp.level or 0)
            pp.save(update_fields=["associated_psychologist", "level"])

        # When request_again -> nothing else (patient can re-request later)
        return Response({"message": f"Request {new_status} successfully"}, status=status.HTTP_200_OK)


# -------------------------
# Doctor's patients list
# -------------------------

class DoctorPatientsView(generics.ListAPIView):
    serializer_class = DoctorViewPatientSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return PatientProfile.objects.filter(associated_psychologist=self.request.user).select_related("user").order_by("user__username")


# -------------------------
# Chatbot session listings
# -------------------------

class ChatbotProfileListView(generics.ListAPIView):
    serializer_class = ChatbotProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["date"]
    ordering_fields = ["date"]

    def get_queryset(self):
        patient_id = self.kwargs.get("patient_id")
        return ChatbotProfile.objects.filter(patient_id=patient_id).order_by("-date")


class ImportantMessagesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, patient_id):
        entries = ChatbotProfile.objects.filter(
            patient_id=patient_id,
            important_messages__isnull=False
        ).order_by("-date")
        serializer = ChatbotProfileSerializer(entries, many=True)
        return Response(serializer.data)


# -------------------------
# Update doctor summary
# -------------------------

class UpdateDoctorSummaryView(APIView):
    """
    Allows doctors to update the `doctor_summary` field for a session.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, session_id):
        session = get_object_or_404(Calendar, id=session_id)

        if session.doctor != request.user:
            return Response(
                {"error": "You are not authorized to update this session."},
                status=status.HTTP_403_FORBIDDEN,
            )

        doctor_summary = (request.data.get("doctor_summary") or "").strip()
        if not doctor_summary:
            return Response(
                {"error": "Doctor summary cannot be empty."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        session.doctor_summary = doctor_summary
        session.save()
        return Response({"message": "Doctor summary updated successfully."}, status=status.HTTP_200_OK)


class DoctorMeProfileView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            doc = Doctor.objects.get(user=request.user)
        except Doctor.DoesNotExist:
            return Response({"error": "Doctor profile not found."}, status=status.HTTP_404_NOT_FOUND)

        pi = dict(doc.professional_information or {})
        data = {
            "display_name": pi.get("display_name", f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username),
            "email": request.user.email,
            "phone": pi.get("phone", ""),
            "specialization": pi.get("specialization", ""),
            "experience": pi.get("experience", ""),
            "qualifications": pi.get("qualifications", ""),
            "description": pi.get("description", ""),
            "organization": pi.get("organization", ""),
            "location": pi.get("location", ""),
        }
        return Response(data, status=status.HTTP_200_OK)


# -------------------------
# NEW: Rate a doctor (by Doctor.id)
# -------------------------

class DoctorRateView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, doctor_id):
        if getattr(request.user, "user_type", "") != "patient":
            return Response({"detail": "Only patients can submit ratings."},
                            status=status.HTTP_403_FORBIDDEN)

        # accept either "rating" or "stars"
        raw = request.data.get("rating", request.data.get("stars", 0))
        try:
            stars = int(raw)
        except (TypeError, ValueError):
            stars = 0

        if stars < 1 or stars > 5:
            return Response({"detail": "rating must be between 1 and 5"},
                            status=status.HTTP_400_BAD_REQUEST)

        comment = (request.data.get("comment") or "").strip()
        doc = get_object_or_404(Doctor, id=doctor_id)

        obj, created = DoctorRating.objects.get_or_create(
            doctor=doc, patient=request.user,
            defaults={"stars": stars, "comment": comment or None}
        )
        if not created:
            obj.stars = stars
            if comment:
                obj.comment = comment
            obj.save()

        agg = DoctorRating.objects.filter(doctor=doc).aggregate(avg=Avg("stars"), cnt=Count("id"))
        avg = float(agg["avg"] or 0.0)
        cnt = int(agg["cnt"] or 0)

        pi = dict(doc.professional_information or {})
        pi["rating"] = round(avg, 1)
        doc.professional_information = pi
        doc.save(update_fields=["professional_information"])

        return Response({"doctor_id": doc.id, "average": round(avg, 1), "count": cnt}, status=status.HTTP_200_OK)
    
    # Reschedule session
    # doctors/views.py
class RescheduleDoctorSessionView(APIView):
    """
    Allows doctor to update/reschedule an existing session.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, session_id):
        data = request.data
        title = data.get("title", "").strip()
        description = data.get("description", "").strip()
        date = data.get("date")

        # Validate
        if not (title and date):
            return Response({"error": "Missing required fields."}, status=400)

        session = get_object_or_404(Calendar, id=session_id)

        # Ensure this doctor owns the session
        if session.doctor != request.user:
            return Response({"error": "Not authorized"}, status=403)

        session.title = title
        session.description = description
        session.date = date
        session.save()

        return Response({"message": "Session rescheduled successfully.", "session_id": session.id}, status=200)

class DeleteDoctorSessionView(APIView):
    """
    DELETE an existing session owned by the authenticated doctor.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, session_id):
        session = get_object_or_404(Calendar, id=session_id)

        # ensure the session belongs to this doctor
        if session.doctor != request.user:
            return Response({"error": "You are not authorized to delete this session."},
                            status=status.HTTP_403_FORBIDDEN)

        session.delete()
        return Response({"message": "Session deleted successfully."}, status=status.HTTP_200_OK)
    
# -------------------------
# NEW: Current Psychologist endpoint
# -------------------------

class CurrentPsychologistView(APIView):
    """
    GET the current psychologist for the logged-in user.
    - If user is a PATIENT: returns their associated_psychologist (Doctor row)
    - If user is a DOCTOR: returns their own Doctor row
    - Otherwise: 404
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user_type = getattr(request.user, "user_type", "")

        if user_type == "patient":
            try:
                pp = PatientProfile.objects.select_related("associated_psychologist").get(user=request.user)
            except PatientProfile.DoesNotExist:
                return Response({"detail": "Patient profile not found."}, status=404)

            if not pp.associated_psychologist:
                return Response({"detail": "No psychologist associated."}, status=404)

            # associated_psychologist is a User; resolve to Doctor row
            try:
                doc = Doctor.objects.select_related("user").get(user=pp.associated_psychologist)
            except Doctor.DoesNotExist:
                return Response({"detail": "Doctor profile not found."}, status=404)

            return Response(CurrentPsychologistSerializer(doc).data, status=200)

        elif user_type == "doctor":
            try:
                doc = Doctor.objects.select_related("user").get(user=request.user)
            except Doctor.DoesNotExist:
                return Response({"detail": "Doctor profile not found."}, status=404)
            return Response(CurrentPsychologistSerializer(doc).data, status=200)

        return Response({"detail": "Unsupported user type."}, status=404)


# -------------------------
# NEW: Latest session endpoint
# -------------------------

class LatestSessionView(APIView):
    """
    Returns the most recent Calendar session for the authenticated user.
    - If user is a patient → last session where patient=request.user
    - If user is a doctor  → last session where doctor=request.user
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        utype = getattr(request.user, "user_type", "")
        if utype == "patient":
            obj = (Calendar.objects
                   .filter(patient=request.user)
                   .order_by("-date")
                   .first())
        else:
            obj = (Calendar.objects
                   .filter(doctor=request.user)
                   .order_by("-date")
                   .first())

        if not obj:
            return Response({"detail": "No sessions found."}, status=404)

        data = LatestSessionSerializer(obj).data
        return Response(data, status=200)
    
class PreviousSessionView(APIView):
    permission_classes = [DRFIsAuthenticated]

    def get(self, request):
        user = request.user
        if user.user_type != "patient":
            return Response({"error": "Only patients can access previous session"}, status=403)

        # All sessions of this patient ordered by date
        sessions = Calendar.objects.filter(patient=user).order_by("date")

        if sessions.count() < 2:
            return Response({"error": "No previous session found"}, status=404)

        # Second-to-last one = previous session
        prev_session = sessions[sessions.count() - 2]
        return Response(LatestSessionSerializer(prev_session).data)