# users/views.py
from decimal import Decimal, InvalidOperation
from datetime import date
import logging
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from django.contrib.auth import get_user_model, authenticate
from django.db import transaction

from rest_framework import views, generics, permissions, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes

from doctors.models import Doctor
from patients.models import PatientProfile
from users.models import Calendar

from .serializers import (
    UserSerializer,
    UserRegistrationSerializer,
    SimpleUserRegistrationSerializer,
    CalendarStaffSerializer,
)
from .permissions import IsStaffUser

log = logging.getLogger(__name__)
User = get_user_model()


# ---------------------------
# Registration & Authentication
# ---------------------------

class UserRegistrationView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        data = {"user": serializer.data, "token": token.key}
        return Response(data, status=status.HTTP_201_CREATED)


class SimpleUserRegistrationView(views.APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = SimpleUserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Registration successful."}, status=status.HTTP_201_CREATED)
        errors = serializer.errors
        first_error = next(iter(errors.values()))[0] if errors else "Registration failed."
        return Response({"message": str(first_error)}, status=status.HTTP_400_BAD_REQUEST)


class LoginView(views.APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        identifier = request.data.get("username")
        password = request.data.get("password")

        if not identifier or not password:
            return Response({"error": "Username/email and password are required"}, status=status.HTTP_400_BAD_REQUEST)

        identifier = identifier.strip().lower()
        try:
            if "@" in identifier:
                user_obj = User.objects.get(email__iexact=identifier)
            else:
                user_obj = User.objects.get(username__iexact=identifier)
        except User.DoesNotExist:
            return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(username=user_obj.username, password=password)
        if not user:
            return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)

        token, _ = Token.objects.get_or_create(user=user)
        user_data = UserSerializer(user).data
        return Response({"token": token.key, "user": user_data})


# ---------------------------
# User detail (self)
# ---------------------------

class UserDetailView(APIView):
    """
    GET /users/user/
    Returns complete user profile with nested doctor/patient/organization data
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        # Base user data
        data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'user_type': getattr(user, 'user_type', ''),
            'date_joined': user.date_joined,
            'last_login': user.last_login,
            'first_name': user.first_name,
            'last_name': user.last_name,
        }

        # Add type-specific profile
        if data['user_type'] == 'doctor':
            try:
                from doctors.models import Doctor
                from doctors.serializers import DoctorProfileSerializer
                doctor = Doctor.objects.select_related('user', 'organization').get(user=user)
                data['doctor_profile'] = DoctorProfileSerializer(doctor).data
            except Doctor.DoesNotExist:
                data['doctor_profile'] = None

        elif data['user_type'] == 'patient':
            try:
                from patients.models import PatientProfile
                pp = PatientProfile.objects.select_related('user', 'associated_psychologist').get(user=user)
                data['patient_profile'] = {
                    'id': pp.id,
                    'level': pp.level,
                    'profile_data': pp.profile_data,
                    'associated_psychologist_id': pp.associated_psychologist.id if pp.associated_psychologist else None,
                }
            except PatientProfile.DoesNotExist:
                data['patient_profile'] = None

        elif data['user_type'] == 'organization':
            try:
                from organizations.models import Organization
                org = Organization.objects.get(user=user)
                data['organization_profile'] = {
                    'id': org.id,
                    'name': org.name,
                    'location': getattr(org, 'location', ''),
                    'details': getattr(org, 'details', {}),
                }
            except Exception:
                data['organization_profile'] = None

        return Response(data, status=status.HTTP_200_OK)


# ---------------------------
# Staff-only
# ---------------------------

class StaffLandingPageView(views.APIView):
    permission_classes = [permissions.IsAuthenticated, IsStaffUser]

    def get(self, request):
        user_data = UserSerializer(request.user).data
        return Response({"user": user_data, "message": "Welcome to your staff dashboard."})


class CalendarListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated, IsStaffUser]
    serializer_class = CalendarStaffSerializer

    def get_queryset(self):
        return Calendar.objects.all()


# ---------------------------
# Profile (GET/PATCH)
# ---------------------------

class MeProfileUpdateView(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    DOCTOR_KEYS = {
        "specialization", "experience", "qualifications", "display_name", "phone",
        "location", "organization", "education", "profile_image", "expertise", "rating",
        "description",
    }

    PATIENT_KEYS = {
        "display_name", "phone", "bio", "location", "age",
        "condition", "emergency_contact", "therapyFocus"
    }

    def _flatten_doctor(self, user, doc):
        pi = dict(doc.professional_information or {})
        return {
            "username": user.username,
            "display_name": pi.get("display_name", (f"{user.first_name} {user.last_name}".strip() or user.username)),
            "email": user.email,
            "phone": pi.get("phone", ""),
            "specialization": pi.get("specialization", ""),
            "experience": pi.get("experience", ""),
            "qualifications": pi.get("qualifications", ""),
            "organization": pi.get("organization", ""),
            "location": pi.get("location", ""),
            "education": pi.get("education", ""),
            "profile_image": pi.get("profile_image", ""),
            "expertise": pi.get("expertise", []),
            "rating": pi.get("rating", 0),
            "description": pi.get("description", ""),
            "rates": str(doc.rates) if doc.rates is not None else "",
            "user_type": "doctor",
        }

    def _flatten_patient(self, user, profile):
        pd = dict(profile.profile_data or {})
        return {
            "username": user.username,
            "display_name": pd.get("display_name", (f"{user.first_name} {user.last_name}".strip() or user.username)),
            "email": user.email,
            "phone": pd.get("phone", ""),
            "age": pd.get("age", ""),
            "condition": pd.get("condition", ""),
            "emergency_contact": pd.get("emergency_contact", ""),
            "location": pd.get("location", ""),
            "therapyFocus": pd.get("therapyFocus", ""),
            "bio": pd.get("bio", ""),
            "user_type": "patient",
        }

    def get(self, request):
        user = request.user
        role = getattr(user, "user_type", "")

        if role == "doctor":
            try:
                doc = Doctor.objects.get(user=user)
            except Doctor.DoesNotExist:
                return Response({"error": "Doctor profile not found."}, status=404)
            return Response(self._flatten_doctor(user, doc), status=200)

        elif role == "patient":
            profile, _ = PatientProfile.objects.get_or_create(user=user)
            return Response(self._flatten_patient(user, profile), status=200)

        return Response({"username": user.username, "email": user.email, "user_type": role}, status=200)

    def patch(self, request):
        user = request.user
        data = request.data.copy()

        # Handle file uploads
        files = request.FILES

        if "email" in data:
            email = (data.get("email") or "").strip().lower()
            if email and email != user.email:
                user.email = email
                user.save(update_fields=["email"])

        if "username" in data:
            new_username = (data.get("username") or "").strip()
            if new_username and new_username.lower() != (user.username or "").lower():
                if User.objects.filter(username__iexact=new_username).exclude(pk=user.pk).exists():
                    return Response({"error": "This username is already taken."}, status=status.HTTP_400_BAD_REQUEST)
                user.username = new_username
                user.save(update_fields=["username"])

        role = getattr(user, "user_type", "")

        if role == "doctor":
            try:
                doc = Doctor.objects.get(user=user)
            except Doctor.DoesNotExist:
                return Response({"error": "Doctor profile not found."}, status=404)

            prof = dict(doc.professional_information or {})
            for k, v in data.items():
                if k in self.DOCTOR_KEYS:
                    prof[k] = v
            doc.professional_information = prof

            # Handle profile image upload
            if "profile_image" in files:
                doc.profile_image = files["profile_image"]

            if "rates" in data:
                raw = str(data.get("rates", "")).strip()
                try:
                    if raw != "":
                        doc.rates = Decimal(raw)
                except (InvalidOperation, TypeError, ValueError):
                    return Response({"error": "Invalid rates value."}, status=status.HTTP_400_BAD_REQUEST)

            doc.save(update_fields=["professional_information", "rates", "profile_image"])
            return Response(self._flatten_doctor(user, doc), status=200)

        elif role == "patient":
            profile, _ = PatientProfile.objects.get_or_create(user=user)
            pd = dict(profile.profile_data or {})
            for k, v in data.items():
                if k in self.PATIENT_KEYS:
                    pd[k] = v
            profile.profile_data = pd

            # Handle profile image upload
            if "profile_image" in files:
                profile.profile_image = files["profile_image"]

            profile.save(update_fields=["profile_data", "profile_image"])
            return Response(self._flatten_patient(user, profile), status=200)

        return Response({"username": user.username, "email": user.email}, status=200)


# ---------------------------
# Account Deletion (role-aware, avoids legacy tables)
# ---------------------------

try:
    from rest_framework_simplejwt.tokens import RefreshToken
    SIMPLEJWT = True
except Exception:
    SIMPLEJWT = False


class DeleteAccountView(views.APIView):
    """
    DELETE /users/account/delete/
    Auth: Token <key>
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        try:
            user = request.user
            role = getattr(user, "user_type", "")

            # Optional JWT blacklist (ignored if not used)
            if SIMPLEJWT:
                refresh = request.data.get("refresh") or request.data.get("refresh_token")
                if refresh:
                    try:
                        token = RefreshToken(refresh)
                        token.blacklist()
                    except Exception:
                        pass

            if role == "patient":
                # Clean Calendars and PatientProfile (safe, ours)
                try:
                    Calendar.objects.filter(patient=user).delete()
                except Exception as e:
                    log.warning("Delete patient calendars failed: %s", e)

                try:
                    PatientProfile.objects.filter(user=user).delete()
                except Exception as e:
                    log.warning("Delete patient profile failed: %s", e)

            elif role == "doctor":
                # Unassign this doctor from patients, clean calendars and doctor profile
                try:
                    PatientProfile.objects.filter(associated_psychologist=user).update(associated_psychologist=None)
                except Exception as e:
                    log.warning("Unassign associated patients failed: %s", e)

                try:
                    Calendar.objects.filter(doctor=user).delete()
                except Exception as e:
                    log.warning("Delete doctor calendars failed: %s", e)

                try:
                    Doctor.objects.filter(user=user).delete()
                except Exception as e:
                    log.warning("Delete doctor profile failed: %s", e)

            # Finally delete user
            user.delete()
            return Response({"detail": "Account deleted."}, status=status.HTTP_200_OK)

        except Exception as e:
            log.exception("DeleteAccountView failed")
            return Response({"detail": f"Server error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ChangePasswordView(views.APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        current_password = request.data.get("current_password") or ""
        new_password = request.data.get("new_password") or ""

        if not current_password or not new_password:
            return Response({"error": "Both current_password and new_password are required."},
                            status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        if not user.check_password(current_password):
            return Response({"error": "Current password is incorrect."}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        return Response({"detail": "Password updated successfully."}, status=status.HTTP_200_OK)


class ChangeEmailView(views.APIView):
    """
    POST /users/patient/change-email/
    POST /users/doctor/change-email/
    Body: {"current_email": "...", "new_email": "..."}
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        current_email = (request.data.get("current_email") or "").strip().lower()
        new_email = (request.data.get("new_email") or "").strip().lower()

        if not current_email or not new_email:
            return Response({"error": "Both current_email and new_email are required."},
                            status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        if (user.email or "").strip().lower() != current_email:
            return Response({"error": "Current email does not match your account email."},
                            status=status.HTTP_400_BAD_REQUEST)

        if current_email == new_email:
            return Response({"error": "New email must be different from current email."},
                            status=status.HTTP_400_BAD_REQUEST)

        # (Optional) uniqueness check
        # if User.objects.filter(email=new_email).exclude(id=user.id).exists():
        #     return Response({"error": "Email already in use."}, status=status.HTTP_400_BAD_REQUEST)

        user.email = new_email
        user.save(update_fields=["email"])
        return Response({"detail": "Email updated successfully.", "email": user.email}, status=status.HTTP_200_OK)
