
from django.db.models.signals import post_save
from django.dispatch import receiver

"""
Notification signals.

This module contains signal handlers that automatically create notifications
when certain events occur (reschedule requests, approvals, doctor requests, etc.)

Signal Flow:
1. Model save triggers post_save signal
2. Signal handler checks if notification is needed
3. Notification.create_notification() is called
4. User sees notification in their bell icon

IMPORTANT: This file must be imported in apps.py ready() method!
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.conf import settings

from .models import Notification


# -------------------------
# Reschedule Request Signals
# -------------------------

# We need to import RescheduleRequest - but it's in doctors app
# To avoid circular imports, we import inside the function

@receiver(post_save, sender='doctors.RescheduleRequest')
def notify_on_reschedule_request(sender, instance, created, **kwargs):
    """
    When a reschedule request is created or updated, send appropriate notifications.
    
    - Created (pending): Notify doctor
    - Approved: Notify patient
    - Rejected: Notify patient
    - Cancelled: Notify doctor (optional)
    """
    # Import here to avoid circular imports
    from doctors.models import RescheduleRequest
    
    calendar_session = instance.calendar_session
    patient = calendar_session.patient
    doctor = calendar_session.doctor
    
    # Get display names
    patient_name = _get_display_name(patient)
    doctor_name = _get_display_name(doctor)
    
    # Format proposed datetime for message
    if isinstance(instance.proposed_date, str):
        proposed_datetime = instance.proposed_date
    else:
        proposed_datetime = instance.proposed_date.strftime("%B %d, %Y")
    if instance.proposed_time:
        if isinstance(instance.proposed_time, str):
            proposed_datetime += f" at {instance.proposed_time}"
        else:
            proposed_datetime += f" at {instance.proposed_time.strftime('%I:%M %p').lstrip('0')}"
    
    if created:
        # New reschedule request - notify doctor
        Notification.create_notification(
            recipient=doctor,
            notification_type='reschedule_request',
            title='Reschedule Request',
            message=f'{patient_name} has requested to reschedule their session to {proposed_datetime}.',
            sender=patient,
            related_calendar=calendar_session,
            metadata={
                'reschedule_request_id': instance.id,
                'proposed_date': str(instance.proposed_date),
                'proposed_time': str(instance.proposed_time) if instance.proposed_time else None,
                'current_date': str(instance.current_date),
                'reason': instance.reason,
            }
        )
    else:
        # Status changed - check what happened
        if instance.status == 'approved':
            # Notify patient of approval
            Notification.create_notification(
                recipient=patient,
                notification_type='reschedule_approved',
                title='Reschedule Approved',
                message=f'Dr. {doctor_name} has approved your reschedule request. Your session is now scheduled for {proposed_datetime}.',
                sender=doctor,
                related_calendar=calendar_session,
                metadata={
                    'reschedule_request_id': instance.id,
                    'new_date': str(instance.proposed_date),
                    'new_time': str(instance.proposed_time) if instance.proposed_time else None,
                    'response_note': instance.response_note,
                }
            )
        
        elif instance.status == 'rejected':
            # Notify patient of rejection
            message = f'Dr. {doctor_name} was unable to accommodate your reschedule request.'
            if instance.response_note:
                message += f' Note: {instance.response_note}'
            
            Notification.create_notification(
                recipient=patient,
                notification_type='reschedule_rejected',
                title='Reschedule Request Declined',
                message=message,
                sender=doctor,
                related_calendar=calendar_session,
                metadata={
                    'reschedule_request_id': instance.id,
                    'response_note': instance.response_note,
                }
            )
        
        elif instance.status == 'cancelled':
            # Patient cancelled - optionally notify doctor
            Notification.create_notification(
                recipient=doctor,
                notification_type='reschedule_cancelled',
                title='Reschedule Request Cancelled',
                message=f'{patient_name} has cancelled their reschedule request.',
                sender=patient,
                related_calendar=calendar_session,
                metadata={
                    'reschedule_request_id': instance.id,
                }
            )


# -------------------------
# Doctor Request Signals
# -------------------------

@receiver(post_save, sender='doctors.DoctorRequest')
def notify_on_doctor_request(sender, instance, created, **kwargs):
    """
    When a patient requests a doctor or the request is approved/rejected.
    
    - Created (pending): Notify doctor
    - Approved: Notify patient
    - Rejected: Notify patient
    """
    patient = instance.patient
    doctor = instance.doctor
    
    patient_name = _get_display_name(patient)
    doctor_name = _get_display_name(doctor)
    
    if created:
        # New doctor request - notify doctor
        Notification.create_notification(
            recipient=doctor,
            notification_type='patient_request',
            title='New Patient Request',
            message=f'{patient_name} has requested to become your patient.',
            sender=patient,
            metadata={
                'doctor_request_id': instance.id,
                'patient_id': patient.id,
            }
        )
    else:
        # Status changed
        if instance.status == 'approved':
            Notification.create_notification(
                recipient=patient,
                notification_type='patient_request_approved',
                title='Request Approved',
                message=f'Dr. {doctor_name} has accepted your request. You can now book sessions with them.',
                sender=doctor,
                metadata={
                    'doctor_request_id': instance.id,
                    'doctor_id': doctor.id,
                }
            )
        
        elif instance.status == 'rejected':
            Notification.create_notification(
                recipient=patient,
                notification_type='patient_request_rejected',
                title='Request Declined',
                message=f'Dr. {doctor_name} was unable to accept your request at this time.',
                sender=doctor,
                metadata={
                    'doctor_request_id': instance.id,
                }
            )


# -------------------------
# Session/Calendar Signals
# -------------------------

@receiver(post_save, sender='users.Calendar')
def notify_on_session_change(sender, instance, created, **kwargs):
    """
    When a session is created or updated.
    
    - Created: Notify patient
    - Updated: Could notify relevant party (not implemented yet)
    """
    patient = instance.patient
    doctor = instance.doctor
    
    if not patient or not doctor:
        return
    
    doctor_name = _get_display_name(doctor)
    
    if created:
        # New session created - notify patient
        if isinstance(instance.date, str):
            date_str = instance.date if instance.date else "TBD"
        else:
            date_str = instance.date.strftime("%B %d, %Y") if instance.date else "TBD"
        
        Notification.create_notification(
            recipient=patient,
            notification_type='session_created',
            title='New Session Scheduled',
            message=f'A new session has been scheduled with Dr. {doctor_name} for {date_str}.',
            sender=doctor,
            related_calendar=instance,
            metadata={
                'session_id': instance.id,
                'session_date': str(instance.date) if instance.date else None,
            }
        )


# -------------------------
# Helper Functions
# -------------------------

def _get_display_name(user):
    """Get a nice display name for a user."""
    if not user:
        return "Unknown"
    
    # Try doctor profile display name
    if hasattr(user, 'doctor_profile'):
        prof_info = getattr(user.doctor_profile, 'professional_information', {}) or {}
        display_name = prof_info.get('display_name')
        if display_name:
            return display_name
    
    # Try patient profile display name
    if hasattr(user, 'patient_profile'):
        profile_data = getattr(user.patient_profile, 'profile_data', {}) or {}
        display_name = profile_data.get('display_name')
        if display_name:
            return display_name
    
    # Try full name
    full_name = f"{user.first_name} {user.last_name}".strip()
    if full_name:
        return full_name
    
    # Fallback to username
    return user.username