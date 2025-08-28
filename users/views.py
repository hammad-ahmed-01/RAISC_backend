from django.contrib.auth import get_user_model, authenticate
from rest_framework import views, generics, permissions, status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .serializers import (
    UserSerializer,
    UserRegistrationSerializer,
    SimpleUserRegistrationSerializer,
    CalendarStaffSerializer,
)
from .permissions import IsStaffUser, IsAuthenticated
from users.models import Calendar

User = get_user_model()


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
        identifier = request.data.get("username")  # could be username OR email
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


class UserDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class StaffLandingPageView(views.APIView):
    permission_classes = [IsAuthenticated, IsStaffUser]

    def get(self, request):
        user_data = UserSerializer(request.user).data
        return Response({"user": user_data, "message": "Welcome to your staff dashboard."})


class CalendarListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsStaffUser]
    serializer_class = CalendarStaffSerializer

    def get_queryset(self):
        return Calendar.objects.all()
