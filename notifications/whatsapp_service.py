# notifications/whatsapp_service.py
"""
WhatsApp Notification Service using Twilio WhatsApp API

SETUP INSTRUCTIONS:
==================
1. Create Twilio account: https://www.twilio.com/try-twilio
2. Go to Console → Messaging → Try it Out → WhatsApp
3. Note your sandbox number and join code
4. Have the doctor send "join <code>" to the sandbox number from their WhatsApp

Add to your .env file:
    TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    TWILIO_AUTH_TOKEN=your_auth_token_here
    TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
    WHATSAPP_ENABLED=true

Install Twilio:
    pip install twilio
"""

import os
import logging
from typing import Optional, Dict, Any
from dotenv import load_dotenv
load_dotenv()
logger = logging.getLogger(__name__)

# Try to import Twilio
try:
    from twilio.rest import Client
    from twilio.base.exceptions import TwilioRestException
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    logger.warning("Twilio not installed. Run: pip install twilio")


class WhatsAppService:
    """
    Service for sending WhatsApp notifications via Twilio.
    """
    
    def __init__(self):
        self.enabled = False
        self.client = None
        self.from_number = None
        self._initialize()
    
    def _initialize(self):
        """Initialize the Twilio client"""
        if not TWILIO_AVAILABLE:
            logger.warning("Twilio library not available")
            return
        
        account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
        auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
        whatsapp_number = os.environ.get('TWILIO_WHATSAPP_NUMBER')
        enabled_flag = os.environ.get('WHATSAPP_ENABLED', 'false').lower() == 'true'
        
        if not all([account_sid, auth_token, whatsapp_number]):
            logger.info("WhatsApp credentials not configured")
            return
        
        if not enabled_flag:
            logger.info("WhatsApp is disabled via WHATSAPP_ENABLED flag")
            return
        
        try:
            self.client = Client(account_sid, auth_token)
            
            # Ensure WhatsApp format for from number
            if whatsapp_number.startswith('whatsapp:'):
                self.from_number = whatsapp_number
            else:
                self.from_number = f"whatsapp:{whatsapp_number}"
            
            self.enabled = True
            logger.info(f"WhatsApp service initialized with number: {self.from_number}")
            
        except Exception as e:
            logger.error(f"Failed to initialize WhatsApp service: {e}")
    
    def format_pakistani_number(self, phone: str) -> Optional[str]:
        """
        Format Pakistani phone number for WhatsApp.
        
        Handles formats:
        - 03001234567 → whatsapp:+923001234567
        - 3001234567 → whatsapp:+923001234567
        - +923001234567 → whatsapp:+923001234567
        - 923001234567 → whatsapp:+923001234567
        """
        if not phone:
            return None
        
        # Remove all non-digit characters except +
        cleaned = ''.join(c for c in str(phone) if c.isdigit() or c == '+')
        
        if not cleaned:
            return None
        
        # Remove leading + for processing
        if cleaned.startswith('+'):
            cleaned = cleaned[1:]
        
        # Handle different Pakistani formats
        if cleaned.startswith('03') and len(cleaned) == 11:
            # 03001234567 → 923001234567
            cleaned = '92' + cleaned[1:]
        elif cleaned.startswith('3') and len(cleaned) == 10:
            # 3001234567 → 923001234567
            cleaned = '92' + cleaned
        elif not cleaned.startswith('92'):
            # Assume Pakistani if no country code
            cleaned = '92' + cleaned
        
        return f"whatsapp:+{cleaned}"
    
    def send_message(self, to_phone: str, message: str) -> Dict[str, Any]:
        """
        Send a WhatsApp message.
        
        Args:
            to_phone: Recipient phone number (Pakistani format)
            message: Message text
            
        Returns:
            Dict with 'success', 'message_sid' or 'error'
        """
        # if not self.enabled:
        #     return {
        #         'success': False, 
        #         'error': 'WhatsApp service not enabled'
        #     }
        
        to_number = self.format_pakistani_number(to_phone)
        print(f"   From number: {self.from_number}")
        print(f"   To number: {to_number}")
        if not to_number:
            return {
                'success': False, 
                'error': f'Invalid phone number: {to_phone}'
            }
        
        try:
            msg = self.client.messages.create(
                from_=self.from_number,
                to=to_number,
                body=message
            )
            
            logger.info(f"WhatsApp sent to {to_number}: SID={msg.sid}, Status={msg.status}")
            
            return {
                'success': True,
                'message_sid': msg.sid,
                'status': msg.status,
                'to': to_number
            }
            
        except TwilioRestException as e:
            logger.error(f"Twilio error: {e.code} - {e.msg}")
            return {
                'success': False, 
                'error': f"Twilio error: {e.msg}"
            }
        except Exception as e:
            logger.error(f"WhatsApp send error: {e}")
            return {
                'success': False, 
                'error': str(e)
            }
    
    def get_doctor_phone(self, doctor_user) -> Optional[str]:
        """
        Extract phone number from doctor's profile.
        
        Args:
            doctor_user: User instance (doctor)
            
        Returns:
            Phone number string or None
        """
        try:
            # Get doctor profile
            if hasattr(doctor_user, 'doctor_profile'):
                profile = doctor_user.doctor_profile
                prof_info = getattr(profile, 'professional_information', None)
                
                if prof_info and isinstance(prof_info, dict):
                    phone = prof_info.get('phone')
                    if phone:
                        return phone
            
            # Fallback: check user model directly
            if hasattr(doctor_user, 'phone') and doctor_user.phone:
                return doctor_user.phone
                
        except Exception as e:
            logger.error(f"Error getting doctor phone: {e}")
        
        return None
    
    def notify_doctor_reschedule_request(
        self, 
        doctor_user,
        patient_name: str,
        session_title: str,
        current_date: str,
        proposed_date: str,
        proposed_time: str,
        reason: str = ""
    ) -> Dict[str, Any]:
        """
        Send WhatsApp notification to doctor about a reschedule request.
        
        Args:
            doctor_user: Doctor's User instance
            patient_name: Name of the patient
            session_title: Title of the session
            current_date: Current session date (formatted string)
            proposed_date: Proposed new date (formatted string)
            proposed_time: Proposed new time
            reason: Patient's reason for rescheduling
            
        Returns:
            Dict with result
        """
        phone = self.get_doctor_phone(doctor_user)
        
        if not phone:
            logger.warning(f"No phone number found for doctor {doctor_user.id}")
            return {
                'success': False,
                'error': 'Doctor has no phone number in profile'
            }
        
        # Build the message
        message = self._build_reschedule_message(
            patient_name=patient_name,
            session_title=session_title,
            current_date=current_date,
            proposed_date=proposed_date,
            proposed_time=proposed_time,
            reason=reason
        )
        
        return self.send_message(phone, message)
    
    def _build_reschedule_message(
        self,
        patient_name: str,
        session_title: str,
        current_date: str,
        proposed_date: str,
        proposed_time: str,
        reason: str = ""
    ) -> str:
        """Build the WhatsApp message for reschedule request"""
        
        message = f"""📅 *Reschedule Request*

*Patient:* {patient_name}
*Session:* {session_title}

*Current Date:* {current_date}
*Requested Date:* {proposed_date}
*Requested Time:* {proposed_time}"""

        if reason:
            message += f"\n\n*Reason:* {reason}"
        
        message += "\n\n👉 Please open RAISC to approve or decline this request."
        
        return message


# Create singleton instance
whatsapp_service = WhatsAppService()


# =====================================================
# Convenience functions for easy imports
# =====================================================

def send_whatsapp(to_phone: str, message: str) -> Dict[str, Any]:
    """Send a WhatsApp message"""
    return whatsapp_service.send_message(to_phone, message)


def notify_doctor_reschedule(
    doctor_user,
    patient_name: str,
    session_title: str,
    current_date: str,
    proposed_date: str,
    proposed_time: str,
    reason: str = ""
) -> Dict[str, Any]:
    """Notify doctor about reschedule request via WhatsApp"""
    return whatsapp_service.notify_doctor_reschedule_request(
        doctor_user=doctor_user,
        patient_name=patient_name,
        session_title=session_title,
        current_date=current_date,
        proposed_date=proposed_date,
        proposed_time=proposed_time,
        reason=reason
    )


def is_whatsapp_enabled() -> bool:
    """Check if WhatsApp is enabled"""
    return whatsapp_service.enabled