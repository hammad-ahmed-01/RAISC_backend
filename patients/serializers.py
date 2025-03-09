from rest_framework import serializers
from .models import PatientProfile
from users.models import Calendar
from doctors.models import Doctor
from users.models import User  # Import User model

class PatientProfileSerializer(serializers.ModelSerializer):
    associated_psychologist_name = serializers.SerializerMethodField()  # Custom field for doctor name

    class Meta:
        model = PatientProfile
        fields = ["level", "associated_psychologist", "associated_psychologist_name", "profile_data"]

    def get_associated_psychologist_name(self, obj):
        """
        Retrieve the username of the associated psychologist if assigned.
        """
        if obj.associated_psychologist:
            print("Doctor Object:", obj.associated_psychologist)  # Debugging
            return obj.associated_psychologist.username  # Fetch doctor's name
        print("No associated psychologist found.")
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

