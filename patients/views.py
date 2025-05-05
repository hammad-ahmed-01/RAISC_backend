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

class PatientLandingPageView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsPatientUser]

    def get(self, request):
        user = request.user
        patient_profile = user.patient_profile  # Access the related patient profile
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


User = get_user_model()  # Use the custom User model

class UserProfileView(APIView):
    """
    Handles fetching and updating user profile data using the chatbot_session_id.
    """

    def get_user_by_token(self, token_key):
        """
        Fetch the user associated with the given token key.
        """
        try:
            token = Token.objects.get(key=token_key)
            return token.user
        except Token.DoesNotExist:
            return None

    def get(self, request, chatbot_session_id):
        """
        Fetch the user profile data for the given chatbot_session_id.
        """
        user = self.get_user_by_token(chatbot_session_id)
        if not user:
            return Response({"error": "User not found or invalid token."}, status=status.HTTP_404_NOT_FOUND)

        # Ensure the user is a patient
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
        Store or update the user profile data for the given chatbot_session_id.
        Also saves the latest chatbot session summary into ChatbotProfile without duplication.
        """
        print("Incoming request data:", request.data)  # Debugging statement
        user = self.get_user_by_token(chatbot_session_id)
        if not user:
            return Response({"error": "User not found or invalid token."}, status=status.HTTP_404_NOT_FOUND)

        # Ensure the user is a patient
        if not hasattr(user, 'patient_profile'):
            return Response({"error": "Access denied. Only patients can update profile data."}, status=status.HTTP_403_FORBIDDEN)

        try:
            # Fetch or create the PatientProfile for the user
            profile, created = PatientProfile.objects.get_or_create(user=user)

            # Ensure request.data is a dictionary
            if not isinstance(request.data, dict):
                return Response({"error": "Invalid data format. Expected a JSON object."}, status=status.HTTP_400_BAD_REQUEST)

            # Update the profile_data field
            profile.profile_data.update(request.data)  # Merge incoming data with existing profile_data
            
            # Set patient level to 1 ONLY if it is currently 0
            if profile.level == 0:
                profile.level = 1

            profile.save()

            # Process chatbot past_summaries
            past_summaries = request.data.get("past_summaries", [])
            if past_summaries:
                latest_summary = past_summaries[-1]  # Get the most recent summary
                summary_timestamp = parse_datetime(latest_summary["timestamp"])  # Convert timestamp to datetime object
            
                # Ensure timestamp is rounded to seconds to avoid precision mismatch
                summary_timestamp = summary_timestamp.replace(microsecond=0)
            
                # Check if a similar session summary already exists for this patient
                existing_entry = ChatbotProfile.objects.filter(
                    patient=user, session_summary=latest_summary["summary"]
                ).exists()
            
                if not existing_entry:
                    try:
                        _, created = ChatbotProfile.objects.get_or_create(
                            patient=user,
                            date=summary_timestamp,
                            defaults={
                                "collected_data": latest_summary["emotional_summary"],
                                "session_summary": latest_summary["summary"],
                                "session_start_msg": latest_summary["session_start_msg"],
                                "session_end_msg": latest_summary["session_end_msg"],
                            }
                        )
                        if created:
                            print(f"New ChatbotProfile created for {user.username} at {summary_timestamp}")
                        else:
                            print(f"Duplicate avoided: ChatbotProfile already exists for {user.username} at {summary_timestamp}")
            
                    except IntegrityError:
                        print(f"IntegrityError: Avoided duplicate chatbot summary for {user.username} at {summary_timestamp}")
                else:
                    print(f"Duplicate session summary detected for {user.username}, skipping entry.")
            
            return Response({"message": "Profile data and chatbot summary saved successfully."}, status=status.HTTP_200_OK)
            

        except Exception as e:
            print(f"Error updating profile data: {e}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    

class PatientSessionsView(generics.ListAPIView):
    serializer_class = CalendarPatientSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Fetch therapy sessions for the logged-in patient.
        """
        return Calendar.objects.filter(patient=self.request.user).order_by("date")

class DoctorSummaryView(APIView):
    """
    Fetches the latest available doctor summary for a patient using session token.
    """

    def get_user_by_token(self, token_key):
        """
        Fetch the user associated with the given token key.
        """
        try:
            token = Token.objects.get(key=token_key)
            return token.user
        except Token.DoesNotExist:
            return None

    def get(self, request, session_token):
        """
        Retrieve the latest doctor summary from the most recent calendar entry that contains one.
        """
        user = self.get_user_by_token(session_token)
        if not user:
            return Response({"error": "Invalid session token or user not found."}, status=status.HTTP_404_NOT_FOUND)

        # Ensure user is a patient
        if not hasattr(user, 'patient_profile'):
            return Response({"error": "Only patients can retrieve doctor summaries."}, status=status.HTTP_403_FORBIDDEN)

        # Fetch the latest calendar entry where doctor_summary is present
        latest_calendar = (
            Calendar.objects
            .filter(patient=user, doctor_summary__isnull=False)  # Only calendars with doctor summaries
            .exclude(doctor_summary="")  # Ignore empty summaries
            .order_by("-date")  # Get the latest one
            .first()
        )

        if not latest_calendar:
            return Response({"error": "No doctor summary found."}, status=status.HTTP_404_NOT_FOUND)

        return Response({"doctor_summary": latest_calendar.doctor_summary}, status=status.HTTP_200_OK)