from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, generics
from users.permissions import IsDoctorUser, IsAuthenticated
from users.serializers import UserSerializer
from .serializers import DoctorProfileSerializer, CalendarDoctorSerializer
from users.models import Calendar

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
    
class CalendarListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsDoctorUser]

    def get_queryset(self):
        user = self.request.user
        return Calendar.objects.filter(doctor=user)

    def get_serializer_class(self):
        return CalendarDoctorSerializer
