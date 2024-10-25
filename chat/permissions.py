from rest_framework.permissions import BasePermission

class CanAskQuestion(BasePermission):
    """
    Allow anyone (unauthenticated or patients) to ask questions.
    """

    def has_permission(self, request, view):
        if request.method == 'POST':
            return True  # Anyone can ask a question
        return request.user.is_authenticated and request.user.user_type == 'patient'

class CanAnswerQuestion(BasePermission):
    """
    Only doctors can answer questions.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type == 'doctor'

class CanDeleteQuestionOrAnswer(BasePermission):
    """
    Only staff members can delete questions or answers.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type == 'staff'
