from rest_framework.permissions import BasePermission
from rest_framework.permissions import IsAuthenticated

class IsAdminUser(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type == 'admin'

class IsDoctorUser(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type == 'doctor'

class IsPatientUser(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type == 'patient'

class IsPatientOrReadOnly(IsAuthenticated):
    def has_permission(self, request, view):
        is_authenticated = super().has_permission(request, view)
        if request.method == 'POST':
            return is_authenticated and request.user.user_type == 'patient'
        return is_authenticated
