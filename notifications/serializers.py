from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    """Full notification serializer for list/detail views."""
    
    sender_name = serializers.SerializerMethodField()
    time_ago = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = [
            'id',
            'notification_type',
            'title',
            'message',
            'is_read',
            'sender_name',
            'related_calendar',
            'metadata',
            'created_at',
            'time_ago',
        ]
        read_only_fields = fields
    
    def get_sender_name(self, obj):
        """Get sender's display name."""
        if obj.sender:
            # Try to get a nice display name
            if hasattr(obj.sender, 'doctor_profile') and obj.sender.user_type == 'doctor':
                prof_info = getattr(obj.sender.doctor_profile, 'professional_information', {}) or {}
                display_name = prof_info.get('display_name')
                if display_name:
                    return display_name
            
            # Fallback to username
            full_name = f"{obj.sender.first_name} {obj.sender.last_name}".strip()
            return full_name if full_name else obj.sender.username
        return None
    
    def get_time_ago(self, obj):
        """Get human-readable time ago string."""
        from django.utils import timezone
        
        now = timezone.now()
        diff = now - obj.created_at
        
        seconds = diff.total_seconds()
        minutes = seconds / 60
        hours = minutes / 60
        days = hours / 24
        
        if seconds < 60:
            return "just now"
        elif minutes < 60:
            m = int(minutes)
            return f"{m} minute{'s' if m != 1 else ''} ago"
        elif hours < 24:
            h = int(hours)
            return f"{h} hour{'s' if h != 1 else ''} ago"
        elif days < 7:
            d = int(days)
            return f"{d} day{'s' if d != 1 else ''} ago"
        else:
            return obj.created_at.strftime("%b %d, %Y")


class NotificationListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for dropdown/list views."""
    
    time_ago = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = [
            'id',
            'notification_type',
            'title',
            'message',
            'is_read',
            'created_at',
            'time_ago',
        ]
        read_only_fields = fields
    
    def get_time_ago(self, obj):
        """Get human-readable time ago string."""
        from django.utils import timezone
        
        now = timezone.now()
        diff = now - obj.created_at
        
        seconds = diff.total_seconds()
        minutes = seconds / 60
        hours = minutes / 60
        days = hours / 24
        
        if seconds < 60:
            return "just now"
        elif minutes < 60:
            m = int(minutes)
            return f"{m} minute{'s' if m != 1 else ''} ago"
        elif hours < 24:
            h = int(hours)
            return f"{h} hour{'s' if h != 1 else ''} ago"
        elif days < 7:
            d = int(days)
            return f"{d} day{'s' if d != 1 else ''} ago"
        else:
            return obj.created_at.strftime("%b %d, %Y")


class UnreadCountSerializer(serializers.Serializer):
    """Serializer for unread count response."""
    
    unread_count = serializers.IntegerField()