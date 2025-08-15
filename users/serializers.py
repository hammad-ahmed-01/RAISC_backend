from rest_framework import serializers
from .models import User, Calendar
from patients.models import PatientProfile
from doctors.models import Doctor
# Slug for Simple user
from django.utils.text import slugify

class PatientProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientProfile
        fields = ['level', 'associated_psychologist', 'profile_data']

class DoctorProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        fields = ['professional_information', 'chatgroup_nickname', 'rates']

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    user_type = serializers.ChoiceField(choices=User.USER_TYPES)
    patient_profile = PatientProfileSerializer(required=False)
    doctor_profile = DoctorProfileSerializer(required=False)

    class Meta:
        model = User
        fields = ('username', 'password', 'email', 'user_type', 'patient_profile', 'doctor_profile')

    def validate(self, data):
        user_type = data.get('user_type')
        if user_type == 'patient' and 'patient_profile' not in data:
            raise serializers.ValidationError({"patient_profile": "Patient profile data is required for patients."})
        if user_type == 'doctor' and 'doctor_profile' not in data:
            raise serializers.ValidationError({"doctor_profile": "Doctor profile data is required for doctors."})
        return data

    def create(self, validated_data):
        user_type = validated_data.get('user_type')
        password = validated_data.pop('password')
        patient_profile_data = validated_data.pop('patient_profile', None)
        doctor_profile_data = validated_data.pop('doctor_profile', None)

        user = User(**validated_data)
        user.set_password(password)
        user.save()

        if user_type == 'patient' and patient_profile_data:
            PatientProfile.objects.create(user=user, **patient_profile_data)
        elif user_type == 'doctor' and doctor_profile_data:
            Doctor.objects.create(user=user, **doctor_profile_data)
        return user

class UserSerializer(serializers.ModelSerializer):
    patient_profile = serializers.SerializerMethodField()
    doctor_profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'user_type', 'patient_profile', 'doctor_profile']

    def get_patient_profile(self, obj):
        if obj.user_type == 'patient':
            try:
                profile = PatientProfile.objects.get(user=obj)
                return PatientProfileSerializer(profile).data
            except PatientProfile.DoesNotExist:
                return None
        return None

    def get_doctor_profile(self, obj):
        if obj.user_type == 'doctor':
            try:
                profile = Doctor.objects.get(user=obj)
                return DoctorProfileSerializer(profile).data
            except Doctor.DoesNotExist:
                return None
        return None

    def update(self, instance, validated_data):
        patient_profile_data = validated_data.pop('patient_profile', None)
        doctor_profile_data = validated_data.pop('doctor_profile', None)
        instance = super().update(instance, validated_data)

        if instance.user_type == 'patient' and patient_profile_data:
            PatientProfile.objects.update_or_create(user=instance, defaults=patient_profile_data)
        elif instance.user_type == 'doctor' and doctor_profile_data:
            Doctor.objects.update_or_create(user=instance, defaults=doctor_profile_data)

        return instance

class UserLimitedSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']

class CalendarStaffSerializer(serializers.ModelSerializer):
    patient = serializers.SerializerMethodField()
    doctor = serializers.SerializerMethodField()

    class Meta:
        model = Calendar
        fields = ['title', 'details', 'patient', 'doctor']

    def get_patient(self, obj):
        if obj.patient:
            try:
                from patients.serializers import PatientProfileLimitedSerializer
                # Accessing the related field 'patient_profile'
                return PatientProfileLimitedSerializer(obj.patient.patient_profile).data
            except PatientProfile.DoesNotExist:
                return None
        return None

    def get_doctor(self, obj):
        if obj.doctor:
            try:
                from doctors.serializers import DoctorLimitedSerializer
                # Accessing the related field 'doctor_profile'
                return DoctorLimitedSerializer(obj.doctor.doctor_profile).data
            except Doctor.DoesNotExist:
                return None
        return None

# Serializer for Simple user (new-registration)
class SimpleUserRegistrationSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ('full_name', 'email', 'password')

    def validate_email(self, value):
        value = value.lower().strip()
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email is already in use.")
        return value

    def create(self, validated_data):
        full_name = validated_data.pop('full_name').strip()
        email = validated_data.pop('email').strip().lower()
        password = validated_data.pop('password')

        # Split name
        parts = full_name.split()
        first_name = parts[0]
        last_name = " ".join(parts[1:]) if len(parts) > 1 else ""

        # Generate a safe username
        base_username = slugify(full_name.replace(" ", ""))[:30]
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username[:30-len(str(counter))]}{counter}"
            counter += 1

        user = User(username=username, email=email, first_name=first_name, last_name=last_name)
        user.set_password(password)
        user.save()
        return user
