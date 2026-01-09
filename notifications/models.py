from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


# Create your models here.

class Notification(models.Model):
    """
    Notification model for in-app notifications.
    
    Supports various notification types for patient-doctor interactions,
    session management, and system announcements.
    """
    
    NOTIFICATION_TYPES = [
        # Patient-Doctor connection
        ('patient_request', 'Patient Request'),
        ('patient_request_approved', 'Patient Request Approved'),
        ('patient_request_rejected', 'Patient Request Rejected'),
        
        # Reschedule flow
        ('reschedule_request', 'Reschedule Request'),
        ('reschedule_approved', 'Reschedule Approved'),
        ('reschedule_rejected', 'Reschedule Rejected'),
        ('reschedule_cancelled', 'Reschedule Cancelled'),
        
        # Session related
        ('session_reminder', 'Session Reminder'),
        ('session_created', 'Session Created'),
        ('session_cancelled', 'Session Cancelled'),
        ('session_updated', 'Session Updated'),
        
        # Organization
        ('organization_update', 'Organization Update'),
        
        # System
        ('system', 'System Notification'),
    ]
    
    # Core fields
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        help_text='User who receives this notification'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sent_notifications',
        help_text='User who triggered this notification (null for system notifications)'
    )
    
    # Notification content
    notification_type = models.CharField(
        max_length=30,
        choices=NOTIFICATION_TYPES,
        default='system'
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    
    # Status
    is_read = models.BooleanField(default=False)
    
    # Related objects (nullable - for linking to relevant records)
    related_calendar = models.ForeignKey(
        'users.Calendar',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications',
        help_text='Related session/calendar entry'
    )
    
    # Flexible metadata for extra info (proposed dates, etc.)
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text='Additional data like proposed dates, reasons, etc.'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When this notification should be auto-deleted'
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"{self.notification_type} for {self.recipient.username}: {self.title[:30]}"
    
    def save(self, *args, **kwargs):
        # Auto-set expiration date if enabled and not already set
        if self.expires_at is None:
            auto_delete_enabled = getattr(
                settings, 
                'NOTIFICATION_AUTO_DELETE_ENABLED', 
                True
            )
            auto_delete_days = getattr(
                settings, 
                'NOTIFICATION_AUTO_DELETE_DAYS', 
                30
            )
            
            if auto_delete_enabled:
                self.expires_at = timezone.now() + timedelta(days=auto_delete_days)
        
        super().save(*args, **kwargs)
    
    def mark_as_read(self):
        """Mark notification as read."""
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=['is_read'])
    
    @classmethod
    def create_notification(
        cls,
        recipient,
        notification_type,
        title,
        message,
        sender=None,
        related_calendar=None,
        metadata=None
    ):
        """
        Helper method to create notifications consistently.
        
        Usage:
            Notification.create_notification(
                recipient=doctor_user,
                notification_type='reschedule_request',
                title='Reschedule Request',
                message='Patient John wants to reschedule their session',
                sender=patient_user,
                related_calendar=calendar_instance,
                metadata={'proposed_date': '2025-02-01', 'proposed_time': '14:00'}
            )
        """
        return cls.objects.create(
            recipient=recipient,
            sender=sender,
            notification_type=notification_type,
            title=title,
            message=message,
            related_calendar=related_calendar,
            metadata=metadata or {}
        )
    
    @classmethod
    def get_unread_count(cls, user):
        """Get unread notification count for a user."""
        return cls.objects.filter(recipient=user, is_read=False).count()
    
    @classmethod
    def mark_all_as_read(cls, user):
        """Mark all notifications as read for a user."""
        return cls.objects.filter(recipient=user, is_read=False).update(is_read=True)