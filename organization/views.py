from django.shortcuts import render,get_object_or_404
from rest_framework.views import APIView
from .models import Organization
from doctors.models import Doctor
from .serializers import OrganizationSerializer
from rest_framework.response import Response
from rest_framework import status
from .serializers import OrganizationViewDoctorsSerializer,OrganizationNoOfDoctorsSerielizer
# Create your views here.
class OrganizationList(APIView):
    def get(self, request):
        organization_list=Organization.objects.all()
        serializer=OrganizationSerializer(organization_list,many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        organization=request.data
        serializer=OrganizationSerializer(data=organization)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_201_CREATED)

class OrganizationDetails(APIView):
    def get(self, request, pk):
        organization=get_object_or_404(Organization,id=pk)
        serializer=OrganizationSerializer(organization)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def put(self, request, pk):
        
        organization=get_object_or_404(Organization,id=pk)
        serializer=OrganizationSerializer(organization, data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def delete(self, request, pk):
        organization=get_object_or_404(Organization,id=pk)
        organization.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    

class OrganizationViewDoctors(APIView):
    def get(self, request, id):
        doctor_list=Doctor.objects.filter(organization_id=id)
        print(list(doctor_list))
        serializer=OrganizationViewDoctorsSerializer(doctor_list, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
        
class OrganizationNoOfDoctors(APIView):
    def get(self,request,pk):
        queryset=Organization.objects.filter(id=pk)
        serializer=OrganizationNoOfDoctorsSerielizer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)