from rest_framework import generics, permissions
from .models import Resource
from .serializers import ResourceSerializer

class ResourceListView(generics.ListAPIView):
    serializer_class = ResourceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        user_condition = user.profile.condition
        return Resource.objects.filter(condition=user_condition)
