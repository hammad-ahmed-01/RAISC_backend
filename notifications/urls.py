from django.urls import path
from .views import (
    NotificationListView,
    NotificationDetailView,
    UnreadCountView,
    MarkAsReadView,
    MarkAllAsReadView,
    DeleteNotificationView,
    CreateTestNotificationView,
)

urlpatterns = [
    # List notifications
    path('', NotificationListView.as_view(), name='notification-list'),
    
    # Unread count (for badge)
    path('unread-count/', UnreadCountView.as_view(), name='notification-unread-count'),
    
    # Mark all as read
    path('mark-all-read/', MarkAllAsReadView.as_view(), name='notification-mark-all-read'),
    
    # Single notification operations
    path('<int:pk>/', NotificationDetailView.as_view(), name='notification-detail'),
    path('<int:pk>/read/', MarkAsReadView.as_view(), name='notification-mark-read'),
    path('<int:pk>/delete/', DeleteNotificationView.as_view(), name='notification-delete'),
    
    # Test endpoint (DEBUG only)
    path('test/', CreateTestNotificationView.as_view(), name='notification-test'),
]