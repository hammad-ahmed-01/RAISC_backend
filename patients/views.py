from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, generics
from users.permissions import IsPatientUser, IsAuthenticated
from users.serializers import UserSerializer
from .serializers import PatientProfileSerializer, CalendarPatientSerializer
from users.models import Calendar
from .models import PatientProfile, ChatbotProfile
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from django.utils.dateparse import parse_datetime
from django.db import IntegrityError
from django.db.models import Q
from rest_framework.authentication import TokenAuthentication

class PatientLandingPageView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsPatientUser]

    def get(self, request):
        user = request.user
        patient_profile = user.patient_profile
        profile_data = PatientProfileSerializer(patient_profile).data
        user_data = UserSerializer(user).data
        data = {
            'user': user_data,
            'patient_profile': profile_data,
            'message': 'Welcome to your patient dashboard.'
        }
        return Response(data)
    
class CalendarListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsPatientUser]

    def get_queryset(self):
        user = self.request.user
        return Calendar.objects.filter(patient=user)

    def get_serializer_class(self):
        return CalendarPatientSerializer


User = get_user_model()

class UserProfileView(APIView):
    """
    Handles fetching and updating user profile data using the chatbot_session_id.
    """

    def get_user_by_token(self, token_key):
        try:
            token = Token.objects.get(key=token_key)
            return token.user
        except Token.DoesNotExist:
            return None

    def get(self, request, chatbot_session_id):
        user = self.get_user_by_token(chatbot_session_id)
        if not user:
            return Response({"error": "User not found or invalid token."}, status=status.HTTP_404_NOT_FOUND)

        if not hasattr(user, 'patient_profile'):
            return Response({"error": "Access denied. Only patients can retrieve profile data."}, status=status.HTTP_403_FORBIDDEN)

        try:
            profile = user.patient_profile
            serializer = PatientProfileSerializer(profile)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except PatientProfile.DoesNotExist:
            return Response({"error": "Patient profile not found."}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, chatbot_session_id):
        """
        Store/merge incoming profile_data and (optionally) save latest chatbot summary.
        """
        user = self.get_user_by_token(chatbot_session_id)
        if not user:
            return Response({"error": "User not found or invalid token."}, status=status.HTTP_404_NOT_FOUND)

        if not hasattr(user, 'patient_profile'):
            return Response({"error": "Access denied. Only patients can update profile data."}, status=status.HTTP_403_FORBIDDEN)

        try:
            profile, _ = PatientProfile.objects.get_or_create(user=user)

            if not isinstance(request.data, dict):
                return Response({"error": "Invalid data format. Expected a JSON object."}, status=status.HTTP_400_BAD_REQUEST)

            # Merge payload into profile_data (now supports age + gender keys too)
            profile.profile_data.update(request.data)

            if profile.level == 0:
                profile.level = 1

            profile.save()

            # Handle optional summaries
            past_summaries = request.data.get("past_summaries", [])
            if past_summaries:
                latest_summary = past_summaries[-1]
                summary_timestamp = parse_datetime(latest_summary["timestamp"]).replace(microsecond=0)

                exists = ChatbotProfile.objects.filter(
                    patient=user, session_summary=latest_summary["summary"]
                ).exists()

                if not exists:
                    try:
                        ChatbotProfile.objects.get_or_create(
                            patient=user,
                            date=summary_timestamp,
                            defaults={
                                "collected_data": latest_summary["emotional_summary"],
                                "session_summary": latest_summary["summary"],
                                "session_start_msg": latest_summary["session_start_msg"],
                                "session_end_msg": latest_summary["session_end_msg"],
                            }
                        )
                    except IntegrityError:
                        pass

            return Response({"message": "Profile data and chatbot summary saved successfully."}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PatientSessionsView(generics.ListAPIView):
    serializer_class = CalendarPatientSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Calendar.objects.filter(patient=self.request.user).order_by("date")


class DoctorSummaryView(APIView):
    """
    Fetches the latest available doctor summary for a patient using session token.
    """

    def get_user_by_token(self, token_key):
        try:
            token = Token.objects.get(key=token_key)
            return token.user
        except Token.DoesNotExist:
            return None

    def get(self, request, session_token):
        user = self.get_user_by_token(session_token)
        if not user:
            return Response({"error": "Invalid session token or user not found."}, status=status.HTTP_404_NOT_FOUND)

        if not hasattr(user, 'patient_profile'):
            return Response({"error": "Only patients can retrieve doctor summaries."}, status=status.HTTP_403_FORBIDDEN)

        latest_calendar = (
            Calendar.objects
            .filter(patient=user, doctor_summary__isnull=False)
            .exclude(doctor_summary="")
            .order_by("-date")
            .first()
        )

        if not latest_calendar:
            return Response({"error": "No doctor summary found."}, status=status.HTTP_404_NOT_FOUND)

        return Response({"doctor_summary": latest_calendar.doctor_summary}, status=status.HTTP_200_OK)
    
class PatientMeProfileView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            pp = PatientProfile.objects.get(user=request.user)
        except PatientProfile.DoesNotExist:
            pp = PatientProfile.objects.create(user=request.user, level=0, profile_data={})

        pd = dict(pp.profile_data or {})
        data = {
            "display_name": pd.get("display_name", f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username),
            "email": request.user.email,
            "phone": pd.get("phone", ""),

            # Added here:
            "age": pd.get("age", ""),
            "gender": pd.get("gender", ""),

            "condition": pd.get("condition", ""),
            "emergency_contact": pd.get("emergency_contact", ""),
            "location": pd.get("location", ""),
            "therapyFocus": pd.get("therapyFocus", ""),
            "chatgroup_nickname": pd.get("chatgroup_nickname", ""),
            "bio": pd.get("bio", ""),
        }
        return Response(data, status=status.HTTP_200_OK)
