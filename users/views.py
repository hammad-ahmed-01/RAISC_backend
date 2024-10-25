from rest_framework import views
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from .serializers import UserSerializer, CalendarStaffSerializer
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from .permissions import IsStaffUser, IsAuthenticated
from users.models import Calendar

from rest_framework import generics, permissions, status
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from .serializers import UserRegistrationSerializer

class UserRegistrationView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        # Register the user using the serializer
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Create a token for the user
        token, created = Token.objects.get_or_create(user=user)
        
        # Return the user data and token in the response
        data = {
            'user': serializer.data,
            'token': token.key
        }
        return Response(data, status=status.HTTP_201_CREATED)


class LoginView(views.APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)
        if user:
            if not Token.objects.filter(user=user).exists():
                Token.objects.create(user=user)
            token = Token.objects.get(user=user)
            user_data = UserSerializer(user).data
            return Response({
                'token': token.key,
                'user': user_data
            })
        else:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)

class UserDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user
    
class StaffLandingPageView(APIView):
    permission_classes = [IsAuthenticated, IsStaffUser]

    def get(self, request):
        user = request.user
        user_data = UserSerializer(user).data
        data = {
            'user': user_data,
            'message': 'Welcome to your staff dashboard.'
        }
        return Response(data)
    
class CalendarListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsStaffUser]

    def get_queryset(self):
        return Calendar.objects.all()

    def get_serializer_class(self):
        return CalendarStaffSerializer
