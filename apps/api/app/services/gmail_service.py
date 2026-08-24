"""
AI Job Hunter — Gmail OAuth2 Service
Handles token exchange, refresh, and sending emails with CV attachments.
"""

import base64
import json
import logging
import httpx
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from pathlib import Path
from typing import Optional, Dict, Any

from app.config import settings

logger = logging.getLogger(__name__)

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GMAIL_SEND_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
GMAIL_PROFILE_URL = "https://gmail.googleapis.com/gmail/v1/users/me/profile"


class GmailService:

    @staticmethod
    async def exchange_code_for_tokens(code: str) -> Optional[Dict[str, Any]]:
        """Exchange the OAuth authorization code for access + refresh tokens."""
        payload = {
            "code": code,
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "redirect_uri": settings.google_redirect_uri,
            "grant_type": "authorization_code",
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(GOOGLE_TOKEN_URL, data=payload)
                if res.status_code == 200:
                    return res.json()
                logger.error(f"Token exchange failed: {res.status_code} {res.text}")
        except Exception as e:
            logger.error(f"Token exchange exception: {e}")
        return None

    @staticmethod
    async def refresh_access_token(refresh_token: str) -> Optional[str]:
        """Refresh an expired access token using the stored refresh token."""
        payload = {
            "refresh_token": refresh_token,
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "grant_type": "refresh_token",
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(GOOGLE_TOKEN_URL, data=payload)
                if res.status_code == 200:
                    return res.json().get("access_token")
                logger.error(f"Token refresh failed: {res.status_code} {res.text}")
        except Exception as e:
            logger.error(f"Token refresh exception: {e}")
        return None

    @staticmethod
    async def get_user_email(access_token: str) -> Optional[str]:
        """Get the authenticated user's Gmail email address."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(
                    GMAIL_PROFILE_URL,
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                if res.status_code == 200:
                    return res.json().get("emailAddress")
        except Exception as e:
            logger.error(f"Failed to get Gmail profile: {e}")
        return None

    @staticmethod
    def _build_email(
        sender_email: str,
        to_email: str,
        subject: str,
        body_html: str,
        cv_path: Optional[str] = None,
        cv_filename: str = "Cv_David_ICT_Specialist.pdf"
    ) -> str:
        """Build a MIME email with optional CV attachment, returns base64url encoded string."""
        msg = MIMEMultipart("mixed")
        msg["From"] = sender_email
        msg["To"] = to_email
        msg["Subject"] = subject

        # Email body
        body_part = MIMEMultipart("alternative")
        body_part.attach(MIMEText(body_html, "html"))
        msg.attach(body_part)

        # Attach CV if path provided and file exists
        if cv_path:
            cv_file = Path(cv_path)
            if cv_file.exists():
                with open(cv_file, "rb") as f:
                    pdf_data = f.read()
                attachment = MIMEApplication(pdf_data, _subtype="pdf")
                attachment.add_header(
                    "Content-Disposition",
                    "attachment",
                    filename=cv_filename
                )
                msg.attach(attachment)
                logger.info(f"CV attached: {cv_filename} ({len(pdf_data)} bytes)")
            else:
                logger.warning(f"CV file not found at path: {cv_path}")

        # Encode to base64url as required by Gmail API
        raw_bytes = msg.as_bytes()
        encoded = base64.urlsafe_b64encode(raw_bytes).decode("utf-8")
        return encoded

    @staticmethod
    async def send_application_email(
        access_token: str,
        sender_email: str,
        to_email: str,
        subject: str,
        body_html: str,
        cv_path: Optional[str] = None,
        cv_filename: str = "Cv_David_ICT_Specialist.pdf"
    ) -> Dict[str, Any]:
        """
        Send a job application email via Gmail API with optional CV attachment.
        Returns dict with status, message_id, and details.
        """
        raw_message = GmailService._build_email(
            sender_email=sender_email,
            to_email=to_email,
            subject=subject,
            body_html=body_html,
            cv_path=cv_path,
            cv_filename=cv_filename
        )

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(
                    GMAIL_SEND_URL,
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json"
                    },
                    json={"raw": raw_message}
                )
                if res.status_code == 200:
                    data = res.json()
                    logger.info(f"Application email sent! Message ID: {data.get('id')} → {to_email}")
                    return {
                        "status": "sent",
                        "message_id": data.get("id"),
                        "to": to_email,
                        "subject": subject
                    }
                else:
                    logger.error(f"Gmail send failed {res.status_code}: {res.text}")
                    return {
                        "status": "failed",
                        "error": res.text,
                        "status_code": res.status_code
                    }
        except Exception as e:
            logger.error(f"Gmail send exception: {e}")
            return {"status": "error", "error": str(e)}
