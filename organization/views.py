from django.shortcuts import render

# Create your views here.
from django.shortcuts import render,get_object_or_404
from rest_framework.views import APIView
from .models import Organization
from doctors.models import Doctor
from users.serializers import OrganizationSerializer, SimpleUserRegistrationSerializer
from rest_framework.response import Response
from rest_framework import status
from .serializers import OrganizationViewDoctorsSerializer,OrganizationNoOfDoctorsSerielizer, OrganizationViewDoctorCalendarSerializer
from rest_framework import permissions
from users.permissions import IsOrganizationUser
from users.models import Calendar
from users.views import UserRegistrationView
from rest_framework.authtoken.models import Token
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
    permission_classes=[permissions.IsAuthenticated, IsOrganizationUser]
    def get(self, request):
        user = request.user
        organization=get_object_or_404(Organization,user_id=user.id)
        serializer=OrganizationSerializer(organization)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def put(self, request):
        user = request.user
        organization=get_object_or_404(Organization,user_id=user.id)
        serializer=OrganizationSerializer(organization, data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def delete(self, request):
        user=request.user
        organization=get_object_or_404(Organization,user_id=user.id)
        organization.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    

class OrganizationViewDoctors(APIView):
    permission_classes=[permissions.IsAuthenticated, IsOrganizationUser]
    def get(self, request):
        
        doctor_list=Doctor.objects.filter(organization_id=request.user.id)
        print(list(doctor_list))
        serializer=OrganizationViewDoctorsSerializer(doctor_list, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
        
class OrganizationNoOfDoctors(APIView):
    permission_classes=[permissions.IsAuthenticated, IsOrganizationUser]
    def get(self,request):
        queryset=Organization.objects.filter(user_id=request.user.id)
        serializer=OrganizationNoOfDoctorsSerielizer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class OrganizationDoctorViewCalendar(APIView):
    permission_classes=[permissions.IsAuthenticated, IsOrganizationUser]
    def get(self, request):
        user=request.user
        doctor_user_ids = Doctor.objects.filter(organization_id=user.id).values_list('user_id', flat=True) #filtering by organization_id of logged in organization and then getting all user_ids of the doctors. Flat=True makes it a set of values instead of queryset/objects.
        #Without flat=True: # Output: <QuerySet [(5,), (8,), (12,)]>
        # This is a list of tuples, even though each tuple has only one value
        #With flat=True:
        # Output: <QuerySet [5, 8, 12]>
        queryset=Calendar.objects.filter(doctor_id__in=doctor_user_ids)
        serializer=OrganizationViewDoctorCalendarSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class OrganizationRegisterDoctor(APIView):
    permission_classes=[permissions.IsAuthenticated, IsOrganizationUser]
    def post(self, request):
        user=request.user
        errors={}
        modified_data=request.data.copy()
        if request.data.get('user_type')=='patient' or request.data.get('user_type')=='organization' :
            errors['error']='Organization can only register doctors'
        #Make the form read only and can only register doctor. 
        if errors:
            return Response({'errors':errors}, status=status.HTTP_400_BAD_REQUEST)
        
        
        if request.data['doctor_profile'].get('organization')!=request.user.id or request.data['doctor_profile'].get('organization')==None:
            modified_data['doctor_profile']['organization']=request.user.id
        print(request.user.id)
        
        serializer = SimpleUserRegistrationSerializer(data=modified_data)
        if serializer.is_valid(raise_exception=True):
            user = serializer.save()
            
            # Create token
            # token, created = Token.objects.get_or_create(user=user)
            
            # Return response
            data = {
                'user': serializer.data,
                # 'token': token.key
            }
            return Response(data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
         
               
        