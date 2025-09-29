from users.serializers import _user_payload
from rest_framework import serializers

from .models import Doctor, DoctorRequest, DoctorRating
from patients.models import PatientProfile, ChatbotProfile
from users.models import Calendar


# ----------------------------
# Doctor list / profile shapes
# ----------------------------


class DoctorProfileSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    # NEW: real-time count of assigned patients
    patients_assigned = serializers.SerializerMethodField()

    class Meta:
        model = Doctor
        fields = [
            "id",
            "user",
            "professional_information",
            "chatgroup_nickname",
            "rates",
            "patients_assigned",  # NEW
        ]

    def get_user(self, obj):
        u = obj.user
        return {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "user_type": getattr(u, "user_type", ""),
            # pass through join/login for convenience if you want (optional)
            "date_joined": getattr(u, "date_joined", None),
            "last_login": getattr(u, "last_login", None),
        }

    def get_patients_assigned(self, obj):
        # Count of patients whose associated_psychologist is this doctor's user
        return PatientProfile.objects.filter(associated_psychologist=obj.user).count()


class DoctorLimitedSerializer(serializers.ModelSerializer):
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
    doctor = serializers.SerializerMethodField()
    requested_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")

    class Meta:
        model = DoctorRequest
        fields = ["id", "patient", "doctor", "status", "requested_at"]

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

    def get_doctor(self, obj):
        try:
            doc = Doctor.objects.get(user=obj.doctor)
            return {
                "id": doc.id,
                "user_id": obj.doctor.id,
                "username": obj.doctor.username,
                "email": obj.doctor.email,
            }
        except Doctor.DoesNotExist:
            return {
                "id": None,
                "user_id": obj.doctor.id,
                "username": obj.doctor.username,
                "email": obj.doctor.email,
            }

# ----------------------------------------
# Calendar sessions shown to the doctor
# ----------------------------------------

class CalendarDoctorSerializer(serializers.ModelSerializer):
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
            "topic",
            "date",
            "session_start_msg",
            "session_end_msg",
        ]


# keep single definition for this serializer
class DoctorProfileSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    class Meta:
        model = Doctor
        fields = ["id", "user", "professional_information", "chatgroup_nickname", "rates"]
        extra_kwargs = {"professional_information": {"required": False}}

    def get_user(self, obj):
        u = obj.user
        return {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "user_type": getattr(u, "user_type", ""),
        }

    def update(self, instance, validated_data):
        prof = validated_data.pop("professional_information", None)
        if prof is not None:
            merged = {**(instance.professional_information or {}), **prof}
            instance.professional_information = merged
        return super().update(instance, validated_data)


# ----------------------
# Rating serializer
# ----------------------

class DoctorRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorRating
        fields = ("stars", "comment")
        extra_kwargs = {
            "stars": {"min_value": 1, "max_value": 5},
            "comment": {"required": False, "allow_blank": True},
        }


# ----------------------
# Current Psychologist
# ----------------------

class CurrentPsychologistSerializer(serializers.ModelSerializer):
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


# ----------------------
# Latest session serializer
# ----------------------

class LatestSessionSerializer(serializers.ModelSerializer):
    session_number = serializers.SerializerMethodField()
    summary = serializers.SerializerMethodField()
    display_datetime = serializers.SerializerMethodField()
    feedback = serializers.SerializerMethodField()

    class Meta:
        model = Calendar
        fields = [
            "id",
            "title",
            "date",
            "description",
            "session_number",
            "summary",
            "display_datetime",
            "feedback",
        ]

    def get_summary(self, obj):
        return obj.doctor_summary or ""

    def get_feedback(self, obj):
        return obj.patient_update or None

    def get_display_datetime(self, obj):
        try:
            return obj.date.strftime("%B %d, %Y – %I:%M %p").lstrip("0").replace(" 0", " ")
        except Exception:
            return None

    def get_session_number(self, obj):
        patient = getattr(obj, "patient", None)
        if not patient:
            return 1
        qs = (Calendar.objects
              .filter(patient=patient, date__lte=obj.date)
              .order_by("date")
              .values_list("id", flat=True))
        try:
            return list(qs).index(obj.id) + 1
        except ValueError:
            return qs.count() or 1
