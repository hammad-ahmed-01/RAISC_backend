from django.shortcuts import render

# Create your views here.
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication

from .models import Notification
from .serializers import (
    NotificationSerializer,
    NotificationListSerializer,
    UnreadCountSerializer,
)


class NotificationListView(generics.ListAPIView):
    """
    GET /api/notifications/
    
    List all notifications for the authenticated user.
    Supports pagination and filtering.
    
    Query params:
    - is_read: true/false - filter by read status
    - limit: number - limit results (default 20)
    - offset: number - pagination offset
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationListSerializer
    
    def get_queryset(self):
        queryset = Notification.objects.filter(recipient=self.request.user)
        
        # Filter by read status if provided
        is_read = self.request.query_params.get('is_read')
        if is_read is not None:
            if is_read.lower() == 'true':
                queryset = queryset.filter(is_read=True)
            elif is_read.lower() == 'false':
                queryset = queryset.filter(is_read=False)
        
        # Limit results
        limit = self.request.query_params.get('limit')
        if limit:
            try:
                limit = int(limit)
                queryset = queryset[:limit]
            except ValueError:
                pass
        
        return queryset


class NotificationDetailView(generics.RetrieveDestroyAPIView):
    """
    GET /api/notifications/{id}/
    DELETE /api/notifications/{id}/
    
    Retrieve or delete a specific notification.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer
    
    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)


class UnreadCountView(APIView):
    """
    GET /api/notifications/unread-count/
    
    Get the count of unread notifications for badge display.
    This endpoint is optimized for frequent polling.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        count = Notification.get_unread_count(request.user)
        return Response({'unread_count': count}, status=status.HTTP_200_OK)


class MarkAsReadView(APIView):
    """
    PATCH /api/notifications/{id}/read/
    
    Mark a single notification as read.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def patch(self, request, pk):
        try:
            notification = Notification.objects.get(
                pk=pk,
                recipient=request.user
            )
        except Notification.DoesNotExist:
            return Response(
                {'error': 'Notification not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        notification.mark_as_read()
        
        return Response(
            {'message': 'Notification marked as read', 'id': pk},
            status=status.HTTP_200_OK
        )


class MarkAllAsReadView(APIView):
    """
    POST /api/notifications/mark-all-read/
    
    Mark all notifications as read for the authenticated user.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        updated_count = Notification.mark_all_as_read(request.user)
        
        return Response(
            {
                'message': 'All notifications marked as read',
                'updated_count': updated_count
            },
            status=status.HTTP_200_OK
        )


class DeleteNotificationView(APIView):
    """
    DELETE /api/notifications/{id}/
    
    Delete a specific notification.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, pk):
        try:
            notification = Notification.objects.get(
                pk=pk,
                recipient=request.user
            )
        except Notification.DoesNotExist:
            return Response(
                {'error': 'Notification not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        notification.delete()
        
        return Response(
            {'message': 'Notification deleted', 'id': pk},
            status=status.HTTP_200_OK
        )


# -----------------------
# Test/Debug Endpoints
# -----------------------

class CreateTestNotificationView(APIView):
    """
    POST /api/notifications/test/
    
    Create a test notification for the authenticated user.
    Only available in DEBUG mode.
    
    Body (optional):
    - title: string
    - message: string
    - notification_type: string
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        from django.conf import settings
        
        if not getattr(settings, 'DEBUG', False):
            return Response(
                {'error': 'Test endpoint only available in DEBUG mode'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        title = request.data.get('title', 'Test Notification')
        message = request.data.get('message', 'This is a test notification.')
        notification_type = request.data.get('notification_type', 'system')
        
        notification = Notification.create_notification(
            recipient=request.user,
            notification_type=notification_type,
            title=title,
            message=message,
            sender=request.user,
        )
        
        serializer = NotificationSerializer(notification)
        return Response(serializer.data, status=status.HTTP_201_CREATED)