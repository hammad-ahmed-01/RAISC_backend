"""
RAISC Email Notification Service (AWS SES)

Mirrors the structure of whatsapp_service.py.
Handles doctor email notifications for patient reschedule requests.

Required .env variables:
    AWS_SES_REGION      e.g. ap-southeast-2
    SENDER_EMAIL        e.g. notifications@raisc.pk  (must be SES-verified)
    EMAIL_ENABLED       true / false
    AWS_ACCESS_KEY_ID     (for SES API access)
    AWS_SECRET_ACCESS_KEY (for SES API access)
"""

import os
import logging
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
log = logging.getLogger(__name__)

load_dotenv()
# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def is_email_enabled() -> bool:
    return os.environ.get("EMAIL_ENABLED", "true").lower() == "true"


# ---------------------------------------------------------------------------
# Service class
# ---------------------------------------------------------------------------

class EmailService:
    def __init__(self):
        self.region     = os.environ.get("AWS_SES_REGION", "ap-southeast-2")
        self.sender     = os.environ.get("SENDER_EMAIL")
        self.enabled    = is_email_enabled()
        self._client    = None  # lazy-initialised

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_client(self):
        if self._client is None:
            self._client = boto3.client("ses", region_name=self.region)
        return self._client

    def _build_reschedule_html(
        self,
        patient_name: str,
        session_title: str,
        current_date: str,
        proposed_date: str,
        proposed_time: str,
        reason: str,
    ) -> str:
        """Return an HTML email body for the reschedule notification."""
        return f"""
        <html>
        <head>
          <style>
            body  {{ font-family: Arial, sans-serif; color: #333; }}
            .box  {{ border-left: 4px solid #4A90D9; padding: 12px 20px;
                     background: #f4f8fd; border-radius: 4px; margin: 20px 0; }}
            h2    {{ color: #4A90D9; }}
            table {{ border-collapse: collapse; width: 100%; margin-top: 10px; }}
            td    {{ padding: 8px 12px; border-bottom: 1px solid #e0e0e0; }}
            td:first-child {{ font-weight: bold; width: 40%; color: #555; }}
            .footer {{ font-size: 12px; color: #999; margin-top: 30px; }}
          </style>
        </head>
        <body>
          <h2>📅 Session Reschedule Request — RAISC</h2>
          <p>A patient has requested to reschedule their upcoming session. 
             Please review the details below and confirm or suggest an alternative.</p>

          <div class="box">
            <table>
              <tr><td>Patient</td><td>{patient_name}</td></tr>
              <tr><td>Session</td><td>{session_title}</td></tr>
              <tr><td>Current Date</td><td>{current_date}</td></tr>
              <tr><td>Proposed Date</td><td>{proposed_date}</td></tr>
              <tr><td>Proposed Time</td><td>{proposed_time}</td></tr>
              <tr><td>Reason</td><td>{reason}</td></tr>
            </table>
          </div>

          <p>Please log in to the RAISC portal to accept or propose a new time.</p>
          <p class="footer">This is an automated notification from RAISC. 
             Do not reply to this email.</p>
        </body>
        </html>
        """

    def _build_reschedule_text(
        self,
        patient_name: str,
        session_title: str,
        current_date: str,
        proposed_date: str,
        proposed_time: str,
        reason: str,
    ) -> str:
        """Return a plain-text fallback for the reschedule notification."""
        return (
            f"RAISC — Session Reschedule Request\n"
            f"{'=' * 40}\n"
            f"Patient      : {patient_name}\n"
            f"Session      : {session_title}\n"
            f"Current Date : {current_date}\n"
            f"Proposed Date: {proposed_date}\n"
            f"Proposed Time: {proposed_time}\n"
            f"Reason       : {reason}\n"
            f"{'=' * 40}\n"
            f"Please log in to the RAISC portal to confirm or suggest a new time.\n"
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def send_reschedule_notification(
        self,
        doctor_email: str,
        patient_name: str,
        session_title: str,
        current_date: str,
        proposed_date: str,
        proposed_time: str,
        reason: str,
    ) -> dict:
        """
        Send a reschedule notification email to the doctor.

        Returns a dict with keys:
            success (bool), message_id (str | None), error (str | None)
        """
        if not self.enabled:
            log.warning("Email service is disabled (EMAIL_ENABLED != true).")
            return {"success": False, "error": "Email service is disabled."}

        if not self.sender:
            log.error("SENDER_EMAIL is not set in environment.")
            return {"success": False, "error": "SENDER_EMAIL not configured."}

        subject  = f"Reschedule Request from {patient_name} — RAISC"
        html_body = self._build_reschedule_html(
            patient_name, session_title, current_date,
            proposed_date, proposed_time, reason,
        )
        text_body = self._build_reschedule_text(
            patient_name, session_title, current_date,
            proposed_date, proposed_time, reason,
        )

        try:
            response = self._get_client().send_email(
                Source=self.sender,
                Destination={"ToAddresses": [doctor_email]},
                Message={
                    "Subject": {"Charset": "UTF-8", "Data": subject},
                    "Body": {
                        "Html": {"Charset": "UTF-8", "Data": html_body},
                        "Text": {"Charset": "UTF-8", "Data": text_body},
                    },
                },
            )
            message_id = response["MessageId"]
            log.info("Reschedule email sent to %s — MessageId: %s", doctor_email, message_id)
            return {"success": True, "message_id": message_id}

        except ClientError as e:
            error_msg = e.response["Error"]["Message"]
            log.error("SES ClientError: %s", error_msg)
            return {"success": False, "error": error_msg}

        except Exception as e:
            log.error("Unexpected error sending email: %s", e)
            return {"success": False, "error": str(e)}


# ---------------------------------------------------------------------------
# Module-level singleton (mirrors whatsapp_service pattern)
# ---------------------------------------------------------------------------

email_service = EmailService()
