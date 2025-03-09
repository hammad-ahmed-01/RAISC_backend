from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, generics
from users.permissions import IsPatientUser, IsAuthenticated
from users.serializers import UserSerializer
from .serializers import PatientProfileSerializer, CalendarPatientSerializer
from users.models import Calendar
from .models import PatientProfile
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny

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

        try:
            profile = user.patient_profile
            serializer = PatientProfileSerializer(profile)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except PatientProfile.DoesNotExist:
            return Response({"error": "Patient profile not found."}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, chatbot_session_id):
        """
        Store or update the user profile data for the given chatbot_session_id.
        """
        print("Incoming request data:", request.data)  # Debugging statement
        user = self.get_user_by_token(chatbot_session_id)
        if not user:
            return Response({"error": "User not found or invalid token."}, status=status.HTTP_404_NOT_FOUND)
    
        try:
            # Fetch or create the PatientProfile for the user
            profile, created = PatientProfile.objects.get_or_create(user=user)
            
            # Ensure request.data is a dictionary
            if not isinstance(request.data, dict):
                return Response({"error": "Invalid data format. Expected a JSON object."}, status=status.HTTP_400_BAD_REQUEST)
            
            # Log current and incoming data
            print("Existing profile_data:", profile.profile_data)
            print("Data to update:", request.data)
    
            # Update the profile_data field
            profile.profile_data.update(request.data)  # Merge incoming data with existing profile_data
            profile.save()
    
            return Response({"message": "Profile data saved successfully."}, status=status.HTTP_200_OK)
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