from django.shortcuts import get_object_or_404
from rest_framework import permissions, generics, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.filters import OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Avg, Count

from users.models import User, Calendar
from patients.models import PatientProfile, ChatbotProfile
from .models import Doctor, DoctorRequest, DoctorRating

from .serializers import (
    DoctorProfileSerializer,
    CalendarDoctorSerializer,
    DoctorRequestSerializer,
    DoctorRequestPostSerializer,
    DoctorViewPatientSerializer,
    ChatbotProfileSerializer,
    DoctorRatingSerializer,  # NEW
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
# Patient ↔ Doctor requests
# -------------------------

class RequestDoctorView(APIView):
    """
    POST /users/doctor/request/<doctor_id>/
    NOTE: <doctor_id> here is the Doctor.pk (not User.pk)
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, doctor_id):
        patient = request.user
        if getattr(patient, "user_type", "") != "patient":
            return Response({"error": "Only patients can request a doctor."}, status=status.HTTP_403_FORBIDDEN)

        doc = get_object_or_404(Doctor, id=doctor_id)
        doctor_user = doc.user

        if DoctorRequest.objects.filter(patient=patient, doctor=doctor_user).exists():
            return Response({"error": "You have already requested this doctor."}, status=status.HTTP_400_BAD_REQUEST)

        req = DoctorRequest.objects.create(patient=patient, doctor=doctor_user)
        return Response(DoctorRequestPostSerializer(req).data, status=status.HTTP_201_CREATED)


class CheckDoctorRequestView(APIView):
    """
    GET /users/doctor/request/<doctor_id>/status/
    NOTE: <doctor_id> is Doctor.pk
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, doctor_id):
        patient = request.user
        if getattr(patient, "user_type", "") != "patient":
            return Response({"error": "Only patients can check requests."}, status=status.HTTP_403_FORBIDDEN)

        doc = get_object_or_404(Doctor, id=doctor_id)
        doctor_user = doc.user

        exists = DoctorRequest.objects.filter(patient=patient, doctor=doctor_user).exists()
        return Response({"requested": exists})


class ListDoctorRequestsView(generics.ListAPIView):
    serializer_class = DoctorRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return DoctorRequest.objects.filter(doctor=self.request.user, status="pending").order_by("-requested_at")


class ManageDoctorRequestView(generics.UpdateAPIView):
    serializer_class = DoctorRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return DoctorRequest.objects.filter(doctor=self.request.user)

    def patch(self, request, *args, **kwargs):
        doctor_request = self.get_object()
        new_status = (request.data.get("status") or "").lower()

        if new_status not in {"approved", "rejected"}:
            return Response({"error": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST)

        doctor_request.status = new_status
        doctor_request.save()

        if new_status == "approved":
            try:
                pp = PatientProfile.objects.get(user=doctor_request.patient)
                pp.associated_psychologist = doctor_request.doctor
                pp.level = max(2, pp.level or 0)
                pp.save()
            except PatientProfile.DoesNotExist:
                return Response({"error": "Patient profile not found"}, status=status.HTTP_404_NOT_FOUND)

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
    """
    POST /users/doctor/rate/<int:doctor_id>/
      body: { "rating": 1..5, "comment": "optional" }

    Upsert patient's rating for this doctor and return {average, count}.
    Also writes the average back into professional_information["rating"] so
    your existing serializers show the updated value everywhere.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, doctor_id):
        if getattr(request.user, "user_type", "") != "patient":
            return Response({"detail": "Only patients can submit ratings."},
                            status=status.HTTP_403_FORBIDDEN)

        try:
            stars = int(request.data.get("rating", 0))
        except (TypeError, ValueError):
            stars = 0
        if stars < 1 or stars > 5:
            return Response({"detail": "rating must be an integer between 1 and 5"},
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