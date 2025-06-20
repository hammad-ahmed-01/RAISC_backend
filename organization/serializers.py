from rest_framework import serializers
from .models import Organization
from doctors.models import Doctor
from patients.models import PatientProfile
class OrganizationSerializer(serializers.ModelSerializer):
    name=serializers.CharField(max_length=255)
    location=serializers.CharField(max_length=255)
    
    class Meta:
        model=Organization
        fields=['id','name','location','details']

class OrganizationViewDoctorsSerializer(serializers.Serializer):
    id=serializers.IntegerField()
    doctor_name=serializers.CharField(source='user.username',max_length=150 )
    no_of_patients=serializers.SerializerMethodField(method_name="get_patient_count")
    
    def get_patient_count(self, doctor:Doctor):
        patient_count=PatientProfile.objects.filter(associated_psychologist_id=doctor.user_id).count()
        return patient_count
    
        
class OrganizationNoOfDoctorsSerielizer(serializers.ModelSerializer):
    no_of_doctors=serializers.SerializerMethodField(method_name='get_doctor_count')
    def get_doctor_count(self, organization: Organization ):
        doctor_count=Doctor.objects.filter(organization_id=organization.id).count()
        return doctor_count
    
    class Meta:
        model=Organization
        fields=['id', 'name','no_of_doctors']
        