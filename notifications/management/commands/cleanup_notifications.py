"""
Management command to clean up expired notifications.

Usage:
    python manage.py cleanup_notifications

This command deletes notifications that have passed their expiration date.
It respects the NOTIFICATION_AUTO_DELETE_ENABLED setting.

Recommended: Run daily via cron job or Celery beat.
Example cron entry (runs at 3 AM daily):
    0 3 * * * cd /path/to/project && python manage.py cleanup_notifications
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone

from notifications.models import Notification


class Command(BaseCommand):
    help = 'Delete expired notifications based on expires_at field'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Run even if NOTIFICATION_AUTO_DELETE_ENABLED is False',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        
        # Check if auto-delete is enabled
        auto_delete_enabled = getattr(
            settings,
            'NOTIFICATION_AUTO_DELETE_ENABLED',
            True
        )
        
        if not auto_delete_enabled and not force:
            self.stdout.write(
                self.style.WARNING(
                    'NOTIFICATION_AUTO_DELETE_ENABLED is False. '
                    'Use --force to run anyway.'
                )
            )
            return
        
        now = timezone.now()
        
        # Find expired notifications
        expired_notifications = Notification.objects.filter(
            expires_at__isnull=False,
            expires_at__lt=now
        )
        
        count = expired_notifications.count()
        
        if count == 0:
            self.stdout.write(
                self.style.SUCCESS('No expired notifications to delete.')
            )
            return
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'DRY RUN: Would delete {count} expired notification(s).'
                )
            )
            
            # Show some details
            for notif in expired_notifications[:10]:
                self.stdout.write(
                    f'  - ID {notif.id}: "{notif.title}" '
                    f'(expired {notif.expires_at})'
                )
            
            if count > 10:
                self.stdout.write(f'  ... and {count - 10} more')
        else:
            # Actually delete
            deleted_count, _ = expired_notifications.delete()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully deleted {deleted_count} expired notification(s).'
                )
            )