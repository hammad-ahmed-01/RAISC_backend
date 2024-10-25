from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, generics
from users.permissions import IsPatientUser, IsAuthenticated
from users.serializers import UserSerializer
from .serializers import PatientProfileSerializer, CalendarPatientSerializer
from users.models import Calendar

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
