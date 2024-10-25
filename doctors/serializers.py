from rest_framework import serializers
from .models import Doctor
from patients.models import PatientProfile
from users.models import Calendar

class DoctorProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        fields = ['professional_information', 'chatgroup_nickname', 'rates']

class DoctorLimitedSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    class Meta:
        model = Doctor
        fields = ['id', 'user']

    def get_user(self, obj):
        from users.serializers import UserLimitedSerializer
        return UserLimitedSerializer(obj.user).data

class CalendarDoctorSerializer(serializers.ModelSerializer):
    patient = serializers.SerializerMethodField()
    class Meta:
        model = Calendar
        fields = ['id', 'title', 'details', 'description', 'patient_update', 'patient']

    def get_patient(self, obj):
        if obj.patient:
            try:
                from patients.serializers import PatientProfileLimitedSerializer
                # Accessing the related field 'patient_profile'
                return PatientProfileLimitedSerializer(obj.patient.patient_profile).data
            except PatientProfile.DoesNotExist:
                return None
        return None
