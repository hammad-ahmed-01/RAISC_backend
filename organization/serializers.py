from rest_framework import serializers

from users.models import Calendar
from .models import Organization
from doctors.models import Doctor
from patients.models import PatientProfile
from doctors.serializers import DoctorProfileSerializer

class OrganizationViewDoctorsSerializer(serializers.Serializer):
    id=serializers.IntegerField()
    doctor_name=serializers.CharField(source='user.username',max_length=150 )
    no_of_patients=serializers.SerializerMethodField(method_name="get_patient_count")
    professional_information = serializers.JSONField(default=dict)
    chatgroup_nickname =serializers.CharField(max_length=255)
    rates = serializers.DecimalField(max_digits=5, decimal_places=2)
    def get_patient_count(self, doctor:Doctor):
        patient_count=PatientProfile.objects.filter(associated_psychologist_id=doctor.user_id).count()
        return patient_count
    
        
class OrganizationNoOfDoctorsSerielizer(serializers.ModelSerializer):
    no_of_doctors=serializers.SerializerMethodField(method_name='get_doctor_count')
    def get_doctor_count(self, organization: Organization ):
        doctor_count=Doctor.objects.filter(organization_id=organization.user_id).count()
        return doctor_count
    
    class Meta:
        model=Organization
        fields=['id', 'name','no_of_doctors']
        
class OrganizationViewDoctorCalendarSerializer(serializers.ModelSerializer):
    
    class Meta:
        model=Calendar
        fields=['id', 'title','date','details', 'description', 'doctor_summary', 'patient_update', 'doctor_id', 'patient_id']


class OrganizationProfileSerializer(serializers.ModelSerializer):
    """Serializer for organization profile with associated doctors"""
    doctors = serializers.SerializerMethodField()
    
    class Meta:
        model = Organization
        fields = ['id', 'name', 'location', 'details', 'user_id', 'doctors']
    
    def get_doctors(self, organization):
        """Get all doctors associated with this organization"""
        doctors = Doctor.objects.filter(organization_id=organization.id)
        return DoctorProfileSerializer(doctors, many=True).data
    