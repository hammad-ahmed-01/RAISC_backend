from rest_framework import serializers
from .models import Doctor, DoctorRequest
from patients.models import PatientProfile, ChatbotProfile
from users.models import Calendar
from users.serializers import UserSerializer

class DoctorProfileSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    class Meta:
        model = Doctor
        fields = ['id','user', 'professional_information', 'chatgroup_nickname', 'rates']
    
    def get_user(self, obj):
        from users.serializers import UserLimitedSerializer
        return UserLimitedSerializer(obj.user).data

class DoctorLimitedSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    class Meta:
        model = Doctor
        fields = ['id', 'user']

    def get_user(self, obj):
        from users.serializers import UserLimitedSerializer
        return UserLimitedSerializer(obj.user).data


class DoctorRequestPostSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source="doctor.username", read_only=True)
    patient_name = serializers.CharField(source="patient.username", read_only=True)

    class Meta:
        model = DoctorRequest
        fields = ["id", "patient", "patient_name", "doctor", "doctor_name", "status", "requested_at"]

class DoctorRequestSerializer(serializers.ModelSerializer):
    patient = serializers.SerializerMethodField()
    requested_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")

    class Meta:
        model = DoctorRequest
        fields = ["id", "patient", "status", "requested_at"]

    def get_patient(self, obj):
        try:
            patient_profile = PatientProfile.objects.get(user=obj.patient)
            return {
                "id": obj.patient.id,
                "username": obj.patient.username,
                "email": obj.patient.email,
                "profile_data": patient_profile.profile_data,  # Extract profile_data from PatientProfile
            }
        except PatientProfile.DoesNotExist:
            return None


class CalendarDoctorSerializer(serializers.ModelSerializer):
    patient = serializers.SerializerMethodField()
    class Meta:
        model = Calendar
        fields = ['id', 'title', 'details', 'date', 'description', 'patient_update', 'doctor_summary', 'patient']

    def get_patient(self, obj):
        if obj.patient:
            try:
                from patients.serializers import PatientProfileLimitedSerializer
                # Accessing the related field 'patient_profile'
                return PatientProfileLimitedSerializer(obj.patient.patient_profile).data
            except PatientProfile.DoesNotExist:
                return None
        return None

class DoctorViewPatientSerializer(serializers.ModelSerializer):
    user = UserSerializer()  # Fetch user details
    profile_data = serializers.JSONField()

    class Meta:
        model = PatientProfile
        fields = ["id", "user", "level", "associated_psychologist", "profile_data"]


class ChatbotProfileSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.username", read_only=True)

    class Meta:
        model = ChatbotProfile
        fields = ["id", "patient", "patient_name", "collected_data", "session_summary", "important_messages", "date", "session_start_msg", "session_end_msg"]
