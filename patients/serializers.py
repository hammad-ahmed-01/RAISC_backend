from rest_framework import serializers
from .models import PatientProfile
from users.models import Calendar
from doctors.models import Doctor

class PatientProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientProfile
        fields = ['level', 'associated_psychologist', 'profile_data']

class PatientProfileLimitedSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    class Meta:
        model = PatientProfile
        fields = ['id', 'user']

    def get_user(self, obj):
        from users.serializers import UserLimitedSerializer
        return UserLimitedSerializer(obj.user).data

class CalendarPatientSerializer(serializers.ModelSerializer):
    doctor = serializers.SerializerMethodField()

    class Meta:
        model = Calendar
        fields = ['title', 'details', 'doctor']

    def get_doctor(self, obj):
        if obj.doctor:
            try:
                from doctors.serializers import DoctorLimitedSerializer
                # Accessing the related field 'doctor_profile'
                return DoctorLimitedSerializer(obj.doctor.doctor_profile).data
            except Doctor.DoesNotExist:
                return None
        return None

