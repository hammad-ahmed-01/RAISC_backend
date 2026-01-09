from django.db import models
from django.conf import settings


class Doctor(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='doctor_profile'
    )
    professional_information = models.JSONField(default=dict)  # stores rating average too
    chatgroup_nickname = models.CharField(max_length=255, blank=True, null=True)
    rates = models.DecimalField(max_digits=7, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return self.user.username
    organization=models.ForeignKey(settings.AUTH_USER_MODEL,null=True, on_delete=models.CASCADE,limit_choices_to={'user_type': 'organization'}, related_name='employed_doctors')



class DoctorRequest(models.Model):
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="doctor_requests",
        limit_choices_to={'user_type': 'patient'}
    )
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="requested_by_patients",
        limit_choices_to={'user_type': 'doctor'}
    )
    status = models.CharField(
        max_length=20,
        choices=[("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected")],
        default="pending"
    )
    requested_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.patient.username} requested {self.doctor.username}"


class DoctorRating(models.Model):
    """
    One row per patient per Doctor (1..5 stars).
    IMPORTANT: This links to the Doctor row (not directly to AUTH_USER).
    """
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name="ratings")
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="doctor_ratings",
        limit_choices_to={'user_type': 'patient'}
    )
    stars = models.PositiveSmallIntegerField()  # integer 1..5
    comment = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (("doctor", "patient"),)
        indexes = [models.Index(fields=["doctor", "patient"])]

    def __str__(self):
        return f"Rating {self.stars} by patient {self.patient_id} for doctor {self.doctor_id}"

class RescheduleRequest(models.Model):
    """
    Model for handling session reschedule requests between patients and doctors.
    
    Flow:
    1. Patient creates a reschedule request with proposed date/time
    2. Doctor receives notification
    3. Doctor approves/rejects the request
    4. Patient receives notification of the decision
    5. If approved, the Calendar session is updated
    """
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),  # Patient cancelled their request
    ]
    
    # The session being rescheduled
    calendar_session = models.ForeignKey(
        'users.Calendar',
        on_delete=models.CASCADE,
        related_name='reschedule_requests',
        help_text='The session to be rescheduled'
    )
    
    # Who requested the reschedule (usually patient, but could be doctor)
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reschedule_requests_made',
        help_text='User who requested the reschedule'
    )
    
    # Current session details (stored for reference)
    current_date = models.DateField(
        help_text='Original session date'
    )
    current_time = models.TimeField(
        null=True,
        blank=True,
        help_text='Original session time (if available)'
    )
    
    # Proposed new schedule
    proposed_date = models.DateField(
        help_text='Proposed new date'
    )
    proposed_time = models.TimeField(
        help_text='Proposed new time'
    )
    
    # Reason for rescheduling
    reason = models.TextField(
        blank=True,
        default='',
        help_text='Reason for requesting reschedule'
    )
    
    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    # Response from doctor
    response_note = models.TextField(
        blank=True,
        default='',
        help_text='Note from doctor when approving/rejecting'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the request was approved/rejected'
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['calendar_session', 'status']),
            models.Index(fields=['requested_by', '-created_at']),
            models.Index(fields=['status', '-created_at']),
        ]
    
    def __str__(self):
        return f"Reschedule request for session {self.calendar_session_id} - {self.status}"
    
    def save(self, *args, **kwargs):
        # Auto-populate current_date from calendar_session if not set
        if not self.current_date and self.calendar_session:
            self.current_date = self.calendar_session.date
        
        super().save(*args, **kwargs)
    
    def approve(self, response_note=''):
        """
        Approve the reschedule request and update the calendar session.
        """
        from django.utils import timezone
        
        if self.status != 'pending':
            raise ValueError(f"Cannot approve request with status: {self.status}")
        
        # Update the calendar session
        self.calendar_session.date = self.proposed_date
        
        # Update time in details if your Calendar model stores time there
        # Or update a time field if it exists
        if hasattr(self.calendar_session, 'details') and isinstance(self.calendar_session.details, dict):
            self.calendar_session.details['time'] = str(self.proposed_time)
            self.calendar_session.details['rescheduled'] = True
            self.calendar_session.details['rescheduled_from'] = str(self.current_date)
        
        self.calendar_session.save()
        
        # Update this request
        self.status = 'approved'
        self.response_note = response_note
        self.responded_at = timezone.now()
        self.save()
        
        return True
    
    def reject(self, response_note=''):
        """
        Reject the reschedule request.
        """
        from django.utils import timezone
        
        if self.status != 'pending':
            raise ValueError(f"Cannot reject request with status: {self.status}")
        
        self.status = 'rejected'
        self.response_note = response_note
        self.responded_at = timezone.now()
        self.save()
        
        return True
    
    def cancel(self):
        """
        Cancel the reschedule request (by the patient).
        """
        if self.status != 'pending':
            raise ValueError(f"Cannot cancel request with status: {self.status}")
        
        self.status = 'cancelled'
        self.save()
        
        return True
    
    @classmethod
    def get_pending_for_doctor(cls, doctor_user):
        """Get all pending reschedule requests for a doctor's sessions."""
        return cls.objects.filter(
            calendar_session__doctor=doctor_user,
            status='pending'
        ).select_related('calendar_session', 'requested_by')
    
    @classmethod
    def get_pending_for_patient(cls, patient_user):
        """Get all pending reschedule requests made by a patient."""
        return cls.objects.filter(
            requested_by=patient_user,
            status='pending'
        ).select_related('calendar_session')
    
    @property
    def is_pending(self):
        return self.status == 'pending'
    
    @property
    def can_be_cancelled(self):
        return self.status == 'pending'