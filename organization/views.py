from urllib import request
from django.shortcuts import render, get_object_or_404
from rest_framework.views import APIView
from .models import Organization
from doctors.models import Doctor
from users.serializers import OrganizationSerializer, SimpleUserRegistrationSerializer
from rest_framework.response import Response
from rest_framework import status
from .serializers import (
    OrganizationViewDoctorsSerializer,
    OrganizationNoOfDoctorsSerielizer,
    OrganizationViewDoctorCalendarSerializer,
    OrganizationProfileSerializer,
)
from rest_framework import permissions
from users.permissions import IsOrganizationUser
from users.models import Calendar
from users.views import UserRegistrationView
from rest_framework.authtoken.models import Token


class OrganizationList(APIView):
    def get(self, request):
        organization_list = Organization.objects.all()
        serializer = OrganizationSerializer(organization_list, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        organization = request.data
        serializer = OrganizationSerializer(data=organization)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_201_CREATED)


class OrganizationDetails(APIView):
    permission_classes = [permissions.IsAuthenticated, IsOrganizationUser]

    def get(self, request):
        user = request.user
        organization, created = Organization.objects.get_or_create(
            user_id=user.id,
            defaults={
                "name": user.username or "Organization",
                "location": "",
                "details": {},
            },
        )
        serializer = OrganizationSerializer(organization)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        user = request.user
        organization, created = Organization.objects.get_or_create(
            user_id=user.id,
            defaults={
                "name": user.username or "Organization",
                "location": "",
                "details": {},
            },
        )
        serializer = OrganizationSerializer(
            organization, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request):
        user = request.user
        try:
            organization = Organization.objects.get(user_id=user.id)
            organization.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Organization.DoesNotExist:
            return Response(
                {"detail": "Organization not found"},
                status=status.HTTP_404_NOT_FOUND,
            )


class OrganizationViewDoctors(APIView):
    permission_classes = [permissions.IsAuthenticated, IsOrganizationUser]

    def get(self, request):
        doctor_list = Doctor.objects.filter(organization_id=request.user.id)
        serializer = OrganizationViewDoctorsSerializer(doctor_list, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class OrganizationNoOfDoctors(APIView):
    permission_classes = [permissions.IsAuthenticated, IsOrganizationUser]

    def get(self, request):
        queryset = Organization.objects.filter(user_id=request.user.id)
        serializer = OrganizationNoOfDoctorsSerielizer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class OrganizationDoctorViewCalendar(APIView):
    permission_classes = [permissions.IsAuthenticated, IsOrganizationUser]

    def get(self, request):
        user = request.user
        doctor_user_ids = Doctor.objects.filter(
            organization_id=user.id
        ).values_list("user_id", flat=True)
        queryset = Calendar.objects.filter(doctor_id__in=doctor_user_ids)
        serializer = OrganizationViewDoctorCalendarSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class OrganizationRegisterDoctor(APIView):
    permission_classes = [permissions.IsAuthenticated, IsOrganizationUser]

    def post(self, request):
        user = request.user
        errors = {}
        modified_data = request.data.copy()

        if request.data.get("user_type") in ("patient", "organization"):
            errors["error"] = "Organization can only register doctors"

        if errors:
            return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        # CRITICAL FIX: Set organization_id to the organization's user_id
        org_id = request.data.get("doctor_profile", {}).get("organization")
        if org_id is None or org_id != request.user.id:
            modified_data.setdefault("doctor_profile", {})
            modified_data["doctor_profile"]["organization"] = request.user.id

        serializer = SimpleUserRegistrationSerializer(data=modified_data)
        serializer.is_valid(raise_exception=True)
        
        # Save the user first
        new_user = serializer.save()
        
        # CRITICAL FIX: Ensure the Doctor model has organization_id set
        try:
            doctor_profile = Doctor.objects.get(user=new_user)
            # Force set organization_id to current organization's user_id
            doctor_profile.organization_id = request.user.id
            doctor_profile.save(update_fields=['organization_id'])
            print(f"✓ Set organization_id={request.user.id} for doctor {doctor_profile.id}")
        except Doctor.DoesNotExist:
            print(f"⚠ Warning: Doctor profile not found for user {new_user.id}")
        
        return Response(
            {
                "message": "Doctor registered successfully",
                "user_id": new_user.id,
                "organization_id": request.user.id
            },
            status=status.HTTP_201_CREATED
        )

class OrganizationProfile(APIView):
    """
    Public API view to get organization details along with associated doctors.
    Returns the organization profile and a list of all doctors employed by the organization.
    No authentication required - public access.
    """
    # CHANGED: Removed permission_classes to make it public
    permission_classes = []  # Public access

    def get(self, request):
        # Get organization_id from query params
        org_id = request.query_params.get('organization_id')
        
        if not org_id:
            return Response(
                {"error": "organization_id parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Fetch by organization user_id
            organization = Organization.objects.get(user_id=org_id)
            serializer = OrganizationProfileSerializer(organization)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Organization.DoesNotExist:
            return Response(
                {"error": "Organization not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except ValueError:
            return Response(
                {"error": "Invalid organization_id format"},
                status=status.HTTP_400_BAD_REQUEST
            )