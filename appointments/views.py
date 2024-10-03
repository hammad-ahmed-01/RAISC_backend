from rest_framework import generics, permissions
from .models import Appointment
from .serializers import AppointmentSerializer
from users.permissions import IsDoctorUser
from users.models import User
from rest_framework.exceptions import PermissionDenied
from rest_framework import serializers

class AppointmentListCreateView(generics.ListCreateAPIView):
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'doctor':
            return Appointment.objects.filter(doctor=user)
        elif user.user_type == 'patient':
            return Appointment.objects.filter(patient=user)
        else:
            return Appointment.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        if user.user_type == 'doctor':
            patient_id = self.request.data.get('patient_id')
            try:
                patient = User.objects.get(id=patient_id, user_type='patient')
            except User.DoesNotExist:
                raise serializers.ValidationError("Patient does not exist.")
            serializer.save(doctor=user, patient=patient)
        else:
            raise PermissionDenied("Only doctors can create appointments.")
