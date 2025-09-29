from users.serializers import _user_payload
from rest_framework import serializers
from .models import PatientProfile
from users.models import Calendar
from doctors.models import Doctor
from users.models import User  # Import User model

class PatientProfileSerializer(serializers.ModelSerializer):
    associated_psychologist_name = serializers.SerializerMethodField()

    class Meta:
        model = PatientProfile
        fields = [
            "level",
            "associated_psychologist",
            "associated_psychologist_name",
            "profile_data",
        ]

    def get_associated_psychologist_name(self, obj):
        if obj.associated_psychologist:
            return obj.associated_psychologist.username
        return None
    
    
class PatientProfileLimitedSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    class Meta:
        model = PatientProfile
        fields = ['id', 'user']

    def get_user(self, obj):
        from users.serializers import UserLimitedSerializer
        return UserLimitedSerializer(obj.user).data

class CalendarPatientSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source="doctor.username", read_only=True)

    class Meta:
        model = Calendar
        fields = ["id", "title", "description", "date", "doctor_name"]

