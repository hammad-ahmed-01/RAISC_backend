from rest_framework import serializers
from django.utils.text import slugify

from organization.models import Organization

from .models import User, Calendar
from patients.models import PatientProfile
from doctors.models import Doctor


# -----------------------
# Embedded profile shapes
# -----------------------
class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model=Organization
        fields=['id','name','location','details','user_id']

class OrganizationProfileSerializer(serializers.ModelSerializer):
    logo = serializers.ImageField(required=False, allow_null=True)
    class Meta:
        model = Organization
        fields = ["name", "location", "details", "logo"]
        
class PatientProfileSerializer(serializers.ModelSerializer):
    profile_image = serializers.ImageField(required=False, allow_null=True)
    class Meta:
        model = PatientProfile
        fields = ["level", "associated_psychologist", "profile_data", "profile_image"]


class DoctorProfileSerializer(serializers.ModelSerializer):
    profile_image = serializers.ImageField(required=False, allow_null=True)
    class Meta:
        model = Doctor
        fields = ["professional_information", "chatgroup_nickname", "rates", "profile_image"]


# -----------------------------------------------
# Generic registration (kept for compatibility)
# -----------------------------------------------

class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Existing generic registration serializer (kept for compatibility).
    """
    password = serializers.CharField(write_only=True)
    user_type = serializers.ChoiceField(choices=User.USER_TYPES)
    patient_profile = PatientProfileSerializer(required=False)
    doctor_profile = DoctorProfileSerializer(required=False)

    class Meta:
        model = User
        fields = ("username", "password", "email", "user_type",
                  "patient_profile", "doctor_profile")

    def validate(self, data):
        user_type = data.get("user_type")
        if user_type == "patient" and "patient_profile" not in data:
            raise serializers.ValidationError(
                {"patient_profile": "Patient profile data is required for patients."}
            )
        if user_type == "doctor" and "doctor_profile" not in data:
            raise serializers.ValidationError(
                {"doctor_profile": "Doctor profile data is required for doctors."}
            )
        return data

    def create(self, validated_data):
        user_type = validated_data.get("user_type")
        password = validated_data.pop("password")
        patient_profile_data = validated_data.pop("patient_profile", None)
        doctor_profile_data = validated_data.pop("doctor_profile", None)

        user = User(**validated_data)
        user.set_password(password)
        user.save()

        if user_type == "patient" and patient_profile_data:
            PatientProfile.objects.create(user=user, **patient_profile_data)
        elif user_type == "doctor" and doctor_profile_data:
            Doctor.objects.create(user=user, **doctor_profile_data)
        return user


# -------------------------
# User read/update payloads
# -------------------------

class UserSerializer(serializers.ModelSerializer):
    patient_profile = serializers.SerializerMethodField()
    doctor_profile = serializers.SerializerMethodField()
    organization_profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "email", "user_type",
                  "patient_profile", "doctor_profile", "organization_profile"]
    def get_patient_profile(self, obj):
        if obj.user_type == "patient":
            try:
                profile = PatientProfile.objects.get(user=obj)
                return PatientProfileSerializer(profile).data
            except PatientProfile.DoesNotExist:
                return None
        return None

    def get_doctor_profile(self, obj):
        if obj.user_type == "doctor":
            try:
                profile = Doctor.objects.get(user=obj)
                return DoctorProfileSerializer(profile).data
            except Doctor.DoesNotExist:
                return None
        return None
    
    def get_organization_profile(self, obj):
        if obj.user_type == "organization":
            try:
                profile = Organization.objects.get(user=obj)
                return OrganizationProfileSerializer(profile).data
            except Organization.DoesNotExist:
                return None
        return None
    

    def update(self, instance, validated_data):
        patient_profile_data = validated_data.pop("patient_profile", None)
        doctor_profile_data = validated_data.pop("doctor_profile", None)
        instance = super().update(instance, validated_data)

        if instance.user_type == "patient" and patient_profile_data:
            PatientProfile.objects.update_or_create(
                user=instance, defaults=patient_profile_data
            )
        elif instance.user_type == "doctor" and doctor_profile_data:
            Doctor.objects.update_or_create(
                user=instance, defaults=doctor_profile_data
            )

        return instance


# -------------------------------------------------------
# Simple Registration (used by /users/new-register/)
# Accepts user_type and doctor_profile in a friendly way
# -------------------------------------------------------

class  SimpleUserRegistrationSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True, min_length=8)
    user_type = serializers.ChoiceField(
        choices=[("patient", "Patient"), ("doctor", "Doctor"),("organization", "Organization")]
    )
    doctor_profile = serializers.DictField(required=False)  # raw dict, normalized in create()
    organization_profile = serializers.DictField(required=False)  
    class Meta:
        model = User
        fields = ("full_name", "email", "password", "user_type", "doctor_profile", "organization_profile")

    def validate_email(self, value):
        value = value.lower().strip()
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email is already in use.")
        return value

    def validate(self, attrs):
        if attrs.get("user_type") == "doctor":
            dp = attrs.get("doctor_profile") or {}
            if not dp.get("specialization"):
                raise serializers.ValidationError(
                    {"doctor_profile": "Specialization is required."}
                )
            if not dp.get("location"):
                raise serializers.ValidationError(
                    {"doctor_profile": "Location is required."}
                )
            rates = dp.get("rates", "")
            try:
                float(str(rates))
            except Exception:
                raise serializers.ValidationError(
                    {"doctor_profile": "Rate must be a number."}
                )
        return attrs

    def create(self, validated_data):
        full_name = validated_data.pop("full_name").strip()
        email = validated_data.pop("email").strip().lower()
        password = validated_data.pop("password")
        user_type = validated_data.pop("user_type")
        dp_in = validated_data.pop("doctor_profile", {}) or {}

        # Split name
        parts = full_name.split()
        first_name = parts[0]
        last_name = " ".join(parts[1:]) if len(parts) > 1 else ""

        # Generate a unique username
        base_username = slugify(full_name.replace(" ", ""))[:30] or "user"
        username = base_username
        i = 1
        while User.objects.filter(username=username).exists():
            suffix = str(i)
            username = f"{base_username[:30 - len(suffix)]}{suffix}"
            i += 1

        # Create user
        user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            user_type=user_type,
        )
        user.set_password(password)
        user.save()

        if user_type == "patient":
            PatientProfile.objects.create(user=user, level=0, profile_data={})
        elif user_type == "organization":
            org_in = validated_data.pop("organization_profile", {}) or {}
            Organization.objects.create(
                user=user,
                name=org_in.get("organization name",""),
                location=org_in.get("location",""),
                details=org_in.get("details",{})
            )
        else:
            # Utilities
            def to_list(v):
                if isinstance(v, list):
                    return [str(x) for x in v]
                return [s.strip() for s in str(v or "").split(",") if s.strip()]

            # NOTE: store "description" (About me); do not store "bio" for doctors anymore
            prof_info = {
                "display_name": dp_in.get("display_name") or full_name,
                "specialization": dp_in.get("specialization", ""),
                "location": dp_in.get("location", ""),
                "experience": dp_in.get("experience", ""),
                "education": dp_in.get("education", ""),
                "expertise": to_list(dp_in.get("expertise")),
                "profile_image": dp_in.get("profile_image", ""),
                "rating": float(dp_in.get("rating", 0) or 0),
                "description": dp_in.get("description", ""),  # <-- NEW
            }
            rates_val = dp_in.get("rates", "0")
            organization_id=dp_in.get("organization")
            print(f"Type: {type(organization_id)}, Value: {organization_id}")
      
            try:
                rates_val = float(str(rates_val))
            except Exception:
                rates_val = 0.0

            Doctor.objects.create(
                user=user,
                professional_information=prof_info,
                chatgroup_nickname="",
                rates=rates_val,
                organization_id=organization_id
            )

        return user


# ----------------------------------
# Staff calendar minimal serializer
# ----------------------------------

class CalendarStaffSerializer(serializers.ModelSerializer):
    """
    Minimal serializer for staff views over Calendar entries.
    """
    class Meta:
        model = Calendar
        fields = "__all__"
