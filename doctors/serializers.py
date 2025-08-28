from rest_framework import serializers

from .models import Doctor, DoctorRequest
from patients.models import PatientProfile, ChatbotProfile
from users.models import Calendar


# ----------------------------
# Doctor list / profile shapes
# ----------------------------

class DoctorProfileSerializer(serializers.ModelSerializer):
    """
    Full doctor profile used on the Doctors page and dashboards.
    Embeds a minimal user dict to avoid circular imports.
    """
    user = serializers.SerializerMethodField()

    class Meta:
        model = Doctor
        fields = ["id", "user", "professional_information", "chatgroup_nickname", "rates"]

    def get_user(self, obj):
        u = obj.user
        return {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "user_type": getattr(u, "user_type", ""),
        }


class DoctorLimitedSerializer(serializers.ModelSerializer):
    """
    Minimal doctor shape (id + minimal user) for compact listings.
    """
    user = serializers.SerializerMethodField()

    class Meta:
        model = Doctor
        fields = ["id", "user"]

    def get_user(self, obj):
        u = obj.user
        return {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "user_type": getattr(u, "user_type", ""),
        }


# ----------------------
# Doctor request shapes
# ----------------------

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
            pp = PatientProfile.objects.get(user=obj.patient)
            return {
                "id": obj.patient.id,
                "username": obj.patient.username,
                "email": obj.patient.email,
                "profile_data": pp.profile_data,
            }
        except PatientProfile.DoesNotExist:
            return {
                "id": obj.patient.id,
                "username": obj.patient.username,
                "email": obj.patient.email,
                "profile_data": {},
            }


# ----------------------------------------
# Calendar sessions shown to the doctor
# ----------------------------------------

class CalendarDoctorSerializer(serializers.ModelSerializer):
    """
    Calendar entries for the doctor, embedding a minimal patient profile.
    """
    patient = serializers.SerializerMethodField()

    class Meta:
        model = Calendar
        fields = [
            "id",
            "title",
            "details",
            "date",
            "description",
            "patient_update",
            "doctor_summary",
            "patient",
        ]

    def get_patient(self, obj):
        if not obj.patient:
            return None
        try:
            pp = PatientProfile.objects.get(user=obj.patient)
            return {
                "user": {
                    "id": obj.patient.id,
                    "username": obj.patient.username,
                    "email": obj.patient.email,
                    "user_type": getattr(obj.patient, "user_type", ""),
                },
                "level": pp.level,
                "associated_psychologist": getattr(pp.associated_psychologist, "id", None),
                "profile_data": pp.profile_data,
            }
        except PatientProfile.DoesNotExist:
            return {
                "user": {
                    "id": obj.patient.id,
                    "username": obj.patient.username,
                    "email": obj.patient.email,
                    "user_type": getattr(obj.patient, "user_type", ""),
                },
                "level": 0,
                "associated_psychologist": None,
                "profile_data": {},
            }


# ----------------------------------------
# Doctor can view a patient's profile
# ----------------------------------------

class DoctorViewPatientSerializer(serializers.ModelSerializer):
    """
    Patient profile shown to a doctor. Embed user as a dict to avoid cross-app imports.
    """
    user = serializers.SerializerMethodField()
    profile_data = serializers.JSONField()

    class Meta:
        model = PatientProfile
        fields = ["id", "user", "level", "associated_psychologist", "profile_data"]

    def get_user(self, obj):
        u = obj.user
        return {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "user_type": getattr(u, "user_type", ""),
        }


# ----------------------------------------
# Chatbot session summaries for a patient
# ----------------------------------------

class ChatbotProfileSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.username", read_only=True)

    class Meta:
        model = ChatbotProfile
        fields = [
            "id",
            "patient",
            "patient_name",
            "collected_data",
            "session_summary",
            "important_messages",
            "date",
            "session_start_msg",
            "session_end_msg",
        ]
