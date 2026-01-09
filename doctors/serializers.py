from rest_framework import serializers

from .models import Doctor, DoctorRequest, DoctorRating
from patients.models import PatientProfile, ChatbotProfile
from users.models import Calendar
import re
from .models import RescheduleRequest
# ----------------------------
# Doctor list / profile shapes
# ----------------------------

class DoctorProfileSerializer(serializers.ModelSerializer):
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
    time = serializers.SerializerMethodField()  # NEW: Add time field

    class Meta:
        model = Calendar
        fields = [
            "id",
            "title",
            "details",
            "date",
            "time",  # NEW
            "description",
            "patient_update",
            "doctor_summary",
            "patient",
        ]

    def _extract_time_from_description(self, obj):
        """
        Extract time from description field.
        Looks for patterns like [time=14:00] or [time=2:00 PM]
        """
        description = obj.description or ""
        
        # Pattern 1: [time=HH:MM] (24-hour format)
        match = re.search(r'\[time=(\d{1,2}:\d{2})\]', description)
        if match:
            return match.group(1)
        
        # Pattern 2: [time=H:MM AM/PM] (12-hour format)
        match = re.search(r'\[time=(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm))\]', description)
        if match:
            time_str = match.group(1).strip().upper()
            try:
                from datetime import datetime
                dt = datetime.strptime(time_str, "%I:%M %p")
                return dt.strftime("%H:%M")
            except ValueError:
                return match.group(1)
        
        # Pattern 3: Check details JSONField
        if hasattr(obj, 'details') and obj.details:
            details = obj.details if isinstance(obj.details, dict) else {}
            if 'time' in details:
                return details['time']
            if 'start_time' in details:
                return details['start_time']
        
        # Default fallback time
        return "14:00"

    def get_time(self, obj):
        """Return time in HH:MM format"""
        return self._extract_time_from_description(obj)

    def get_patient(self, obj):
        if not obj.patient:
            return None
        try:
            from patients.models import PatientProfile
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
    time = serializers.SerializerMethodField()  # NEW: Separate time field

    class Meta:
        model = Calendar
        fields = [
            "id",
            "title",
            "date",
            "time",  # NEW
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

    def _extract_time_from_description(self, obj):
        """
        Extract time from description field.
        Looks for patterns like [time=14:00] or [time=2:00 PM]
        Returns time string in HH:MM format, or None if not found.
        """
        description = obj.description or ""
        
        # Pattern 1: [time=HH:MM] (24-hour format)
        match = re.search(r'\[time=(\d{1,2}:\d{2})\]', description)
        if match:
            return match.group(1)
        
        # Pattern 2: [time=H:MM AM/PM] (12-hour format)
        match = re.search(r'\[time=(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm))\]', description)
        if match:
            time_str = match.group(1).strip().upper()
            # Convert to 24-hour format
            try:
                from datetime import datetime
                dt = datetime.strptime(time_str, "%I:%M %p")
                return dt.strftime("%H:%M")
            except ValueError:
                return match.group(1)
        
        # Pattern 3: Check details JSONField if it exists
        if hasattr(obj, 'details') and obj.details:
            details = obj.details if isinstance(obj.details, dict) else {}
            if 'time' in details:
                return details['time']
            if 'start_time' in details:
                return details['start_time']
        
        return None

    def _format_time_12h(self, time_str):
        """Convert HH:MM to 12-hour format with AM/PM"""
        if not time_str:
            return None
        try:
            # Handle HH:MM format
            parts = time_str.split(':')
            hour = int(parts[0])
            minute = int(parts[1]) if len(parts) > 1 else 0
            
            period = "AM" if hour < 12 else "PM"
            if hour == 0:
                hour = 12
            elif hour > 12:
                hour -= 12
            
            return f"{hour}:{minute:02d} {period}"
        except (ValueError, IndexError):
            return time_str

    def get_time(self, obj):
        """Return time in HH:MM format"""
        return self._extract_time_from_description(obj)

    def get_display_datetime(self, obj):
        """
        Return formatted date and time string.
        Example: "January 15, 2026 – 2:00 PM"
        """
        try:
            # Format the date part
            if obj.date:
                date_str = obj.date.strftime("%B %d, %Y").lstrip("0").replace(" 0", " ")
            else:
                return None
            
            # Get the time part
            time_str = self._extract_time_from_description(obj)
            time_display = self._format_time_12h(time_str)
            
            if time_display:
                return f"{date_str} – {time_display}"
            else:
                return date_str
                
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



class RescheduleRequestSerializer(serializers.ModelSerializer):
    """Full serializer for reschedule requests."""
    
    patient_name = serializers.SerializerMethodField()
    doctor_name = serializers.SerializerMethodField()
    session_title = serializers.CharField(source='calendar_session.title', read_only=True)
    current_date_display = serializers.SerializerMethodField()
    proposed_date_display = serializers.SerializerMethodField()
    
    class Meta:
        model = RescheduleRequest
        fields = [
            'id',
            'calendar_session',
            'session_title',
            'requested_by',
            'patient_name',
            'doctor_name',
            'current_date',
            'current_time',
            'current_date_display',
            'proposed_date',
            'proposed_time',
            'proposed_date_display',
            'reason',
            'status',
            'response_note',
            'created_at',
            'responded_at',
        ]
        read_only_fields = [
            'id', 'created_at', 'responded_at', 
            'patient_name', 'doctor_name', 'session_title',
            'current_date_display', 'proposed_date_display'
        ]
    
    def get_patient_name(self, obj):
        """Get the patient's display name."""
        patient = obj.calendar_session.patient if obj.calendar_session else None
        if patient:
            full_name = f"{patient.first_name} {patient.last_name}".strip()
            return full_name if full_name else patient.username
        return None
    
    def get_doctor_name(self, obj):
        """Get the doctor's display name."""
        doctor = obj.calendar_session.doctor if obj.calendar_session else None
        if doctor:
            # Try to get display name from doctor profile
            if hasattr(doctor, 'doctor_profile'):
                prof_info = getattr(doctor.doctor_profile, 'professional_information', {}) or {}
                display_name = prof_info.get('display_name')
                if display_name:
                    return display_name
            full_name = f"{doctor.first_name} {doctor.last_name}".strip()
            return full_name if full_name else doctor.username
        return None
    
    def get_current_date_display(self, obj):
        """Format current date for display."""
        if obj.current_date:
            return obj.current_date.strftime("%B %d, %Y")
        return None
    
    def get_proposed_date_display(self, obj):
        """Format proposed date for display."""
        if obj.proposed_date:
            date_str = obj.proposed_date.strftime("%B %d, %Y")
            if obj.proposed_time:
                time_str = obj.proposed_time.strftime("%I:%M %p").lstrip('0')
                return f"{date_str} at {time_str}"
            return date_str
        return None


class RescheduleRequestCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating reschedule requests."""
    
    class Meta:
        model = RescheduleRequest
        fields = [
            'calendar_session',
            'proposed_date',
            'proposed_time',
            'reason',
        ]
    
    def validate_calendar_session(self, value):
        """Ensure the session belongs to the requesting user."""
        request = self.context.get('request')
        if request and request.user:
            # Patient can only reschedule their own sessions
            if value.patient != request.user:
                raise serializers.ValidationError(
                    "You can only reschedule your own sessions."
                )
        return value
    
    def validate_proposed_date(self, value):
        """Ensure proposed date is in the future."""
        from django.utils import timezone
        
        if value < timezone.now().date():
            raise serializers.ValidationError(
                "Proposed date must be in the future."
            )
        return value
    
    def validate(self, attrs):
        """Check for existing pending requests."""
        calendar_session = attrs.get('calendar_session')
        
        # Check if there's already a pending request for this session
        existing_pending = RescheduleRequest.objects.filter(
            calendar_session=calendar_session,
            status='pending'
        ).exists()
        
        if existing_pending:
            raise serializers.ValidationError(
                "There is already a pending reschedule request for this session. "
                "Please cancel it before creating a new one."
            )
        
        return attrs
    
    def create(self, validated_data):
        """Create the reschedule request with current date/time from session."""
        request = self.context.get('request')
        calendar_session = validated_data['calendar_session']
        
        # Extract current time from session details if available
        current_time = None
        if hasattr(calendar_session, 'details') and isinstance(calendar_session.details, dict):
            time_str = calendar_session.details.get('time')
            if time_str:
                try:
                    from datetime import datetime
                    current_time = datetime.strptime(time_str, '%H:%M').time()
                except (ValueError, TypeError):
                    pass
        
        return RescheduleRequest.objects.create(
            calendar_session=calendar_session,
            requested_by=request.user,
            current_date=calendar_session.date,
            current_time=current_time,
            proposed_date=validated_data['proposed_date'],
            proposed_time=validated_data['proposed_time'],
            reason=validated_data.get('reason', ''),
        )


class RescheduleRequestResponseSerializer(serializers.Serializer):
    """Serializer for doctor's response to reschedule request."""
    
    action = serializers.ChoiceField(choices=['approve', 'reject'])
    response_note = serializers.CharField(required=False, allow_blank=True, default='')