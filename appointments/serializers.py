from rest_framework import serializers
from .models import Appointment
from users.serializers import UserSerializer

class AppointmentSerializer(serializers.ModelSerializer):
    patient = UserSerializer(read_only=True)
    doctor = UserSerializer(read_only=True)

    class Meta:
        model = Appointment
        fields = ['id', 'patient', 'doctor', 'date_time', 'notes']
