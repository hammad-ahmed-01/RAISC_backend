from rest_framework.permissions import BasePermission, IsAuthenticated

class IsStaffUser(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type == 'staff'

class IsDoctorUser(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type == 'doctor'

class IsPatientUser(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type == 'patient'

class IsPatientOrReadOnly(IsAuthenticated):
    def has_permission(self, request, view):
        is_authenticated = super().has_permission(request, view)
        if request.method in ['POST', 'PUT', 'PATCH']:
            return is_authenticated and request.user.user_type == 'patient'
        return is_authenticated
