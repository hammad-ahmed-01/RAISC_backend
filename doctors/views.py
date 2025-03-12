from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, generics
from users.permissions import IsDoctorUser, IsAuthenticated
from users.serializers import UserSerializer
from .serializers import DoctorProfileSerializer, CalendarDoctorSerializer, DoctorRequestSerializer, DoctorRequestPostSerializer
from users.models import User
from users.models import Calendar
from .models import Doctor, DoctorRequest
from patients.models import PatientProfile, ChatbotProfile
from rest_framework import status
from .serializers import DoctorViewPatientSerializer, ChatbotProfileSerializer
from rest_framework.filters import OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from rest_framework.authentication import TokenAuthentication

class DoctorLandingPageView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsDoctorUser]

    def get(self, request):
        user = request.user
        doctor_profile = user.doctor_profile  # Access the related doctor profile
        profile_data = DoctorProfileSerializer(doctor_profile).data
        user_data = UserSerializer(user).data
        data = {
            'user': user_data,
            'doctor_profile': profile_data,
            'message': 'Welcome to your doctor dashboard.'
        }
        return Response(data)
    
class DoctorSessionsView(generics.ListAPIView):
    serializer_class = CalendarDoctorSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Calendar.objects.filter(doctor=self.request.user)


class ListDoctorsView(generics.ListAPIView):
    queryset = Doctor.objects.select_related("user")  # Fetch related user data
    serializer_class = DoctorProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

class RequestDoctorView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, doctor_id):
        patient = request.user
        if patient.user_type != "patient":
            return Response({"error": "Only patients can request a doctor."}, status=403)

        doctor = User.objects.filter(id=doctor_id, user_type="doctor").first()
        if not doctor:
            return Response({"error": "Doctor not found."}, status=404)

        # Check if a request already exists
        if DoctorRequest.objects.filter(patient=patient, doctor=doctor).exists():
            return Response({"error": "You have already requested this doctor."}, status=400)

        # Create the doctor request
        doctor_request = DoctorRequest.objects.create(patient=patient, doctor=doctor)
        return Response(DoctorRequestPostSerializer(doctor_request).data, status=201)

class CheckDoctorRequestView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, doctor_id):
        patient = request.user
        if patient.user_type != "patient":
            return Response({"error": "Only patients can check requests."}, status=403)

        doctor = User.objects.filter(id=doctor_id, user_type="doctor").first()
        if not doctor:
            return Response({"error": "Doctor not found."}, status=404)

        request_exists = DoctorRequest.objects.filter(patient=patient, doctor=doctor).exists()
        return Response({"requested": request_exists})

# Fetch pending requests for the doctor
class ListDoctorRequestsView(generics.ListAPIView):
    serializer_class = DoctorRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return DoctorRequest.objects.filter(doctor=self.request.user, status="pending")

# Manage request: Approve or Reject
class ManageDoctorRequestView(generics.UpdateAPIView):
    serializer_class = DoctorRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return DoctorRequest.objects.filter(doctor=self.request.user)

    def patch(self, request, *args, **kwargs):
        doctor_request = self.get_object()
        new_status = request.data.get("status")

        if new_status in ["approved", "rejected"]:
            doctor_request.status = new_status
            doctor_request.save()

            # If accepted, update PatientProfile to assign the doctor
            if new_status == "approved":
                try:
                    patient_profile = PatientProfile.objects.get(user=doctor_request.patient)
                    patient_profile.associated_psychologist = doctor_request.doctor  # Assign doctor
                    patient_profile.level = max(2, patient_profile.level)  # Ensure level is at least 2
                    patient_profile.save()
                except PatientProfile.DoesNotExist:
                    return Response({"error": "Patient profile not found"}, status=status.HTTP_404_NOT_FOUND)

            return Response({"message": f"Request {new_status} successfully"}, status=status.HTTP_200_OK)

        return Response({"error": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST)

class DoctorPatientsView(generics.ListAPIView):
    serializer_class = DoctorViewPatientSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return PatientProfile.objects.filter(associated_psychologist=self.request.user)


class ChatbotProfileListView(generics.ListAPIView):
    serializer_class = ChatbotProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["date"]
    ordering_fields = ["date"]

    def get_queryset(self):
        """
        Fetch chatbot profiles for a specific patient.
        """
        patient_id = self.kwargs.get("patient_id")
        return ChatbotProfile.objects.filter(patient_id=patient_id).order_by("-date")


class ImportantMessagesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, patient_id):
        """
        Fetch chatbot entries where important_messages are present.
        """
        chatbot_entries = ChatbotProfile.objects.filter(patient_id=patient_id, important_messages__isnull=False)
        serializer = ChatbotProfileSerializer(chatbot_entries, many=True)
        return Response(serializer.data)

class UpdateDoctorSummaryView(APIView):
    """
    Allows doctors to update the `doctor_summary` field for a session.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, session_id):
        """
        Update the `doctor_summary` field for a specific session.
        """
        # Get the session object
        session = get_object_or_404(Calendar, id=session_id)

        # Ensure that the requesting user is the assigned doctor for this session
        if session.doctor != request.user:
            return Response(
                {"error": "You are not authorized to update this session."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get doctor summary from request
        doctor_summary = request.data.get("doctor_summary", "").strip()

        if not doctor_summary:
            return Response(
                {"error": "Doctor summary cannot be empty."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update and save the session summary
        session.doctor_summary = doctor_summary
        session.save()

        return Response({"message": "Doctor summary updated successfully."}, status=status.HTTP_200_OK)