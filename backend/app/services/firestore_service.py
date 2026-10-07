"""Firestore Lead & Conversation Logging Service.

Records high-intent recruiter interactions into Google Cloud Firestore (Free Tier: 20k writes/day)
and optionally sends instant webhook alerts to Slack or Discord.
"""

import logging
import datetime
from typing import Optional
import httpx

from backend.app.core.config import settings
from backend.app.core.security import UserIdentity

logger = logging.getLogger("portfolio.firestore")


class FirestoreLeadService:
    def __init__(self):
        self._client = None
        self._initialized = False

    def _get_client(self):
        if not self._initialized:
            try:
                from google.cloud import firestore
                self._client = firestore.Client(project=settings.GCP_PROJECT_ID)
                self._initialized = True
            except Exception as e:
                logger.warning(f"Firestore client initialization skipped or failed: {e}")
                self._initialized = True
                self._client = None
        return self._client

    async def record_lead_interaction(
        self,
        user: UserIdentity,
        question: str,
        answer_preview: str
    ):
        """Records the visitor interaction and notifies via webhook if configured."""
        now = datetime.datetime.utcnow().isoformat() + "Z"

        if not user.is_authenticated:
            # For anonymous visitors, we don't spam Firestore, only log telemetry
            logger.info(f"Anonymous interaction from {user.client_ip}: '{question[:50]}'")
            return

        client = self._get_client()
        lead_doc_id = user.uid

        lead_data = {
            "uid": user.uid,
            "email": user.email,
            "name": user.name,
            "picture": user.picture,
            "provider": user.provider,
            "last_active": now,
            "client_ip": user.client_ip,
        }

        # Write lead to Firestore if connected
        if client:
            try:
                doc_ref = client.collection(settings.FIRESTORE_COLLECTION_LEADS).document(lead_doc_id)
                doc_ref.set(lead_data, merge=True)

                # Append conversation record in subcollection
                conv_ref = doc_ref.collection("conversations").document()
                conv_ref.set({
                    "timestamp": now,
                    "question": question,
                    "answer_preview": answer_preview[:200]
                })
                logger.info(f"Captured recruiter lead in Firestore: {user.email or user.uid}")
            except Exception as e:
                logger.error(f"Failed to record lead in Firestore: {e}")

        # Trigger Webhook notification (Discord / Slack) if configured
        if settings.LEAD_NOTIFICATION_WEBHOOK_URL:
            await self._send_webhook_alert(user, question)

    async def _send_webhook_alert(self, user: UserIdentity, question: str):
        webhook_url = settings.LEAD_NOTIFICATION_WEBHOOK_URL
        if not webhook_url:
            return

        text = (
            f"🔔 **New Recruiter / Engineering Lead on Portfolio AI!**\n"
            f"• **Name:** {user.name or 'Anonymous'}\n"
            f"• **Email:** {user.email or 'N/A'}\n"
            f"• **Provider:** {user.provider}\n"
            f"• **Question Asked:** *\"{question}\"*"
        )

        try:
            async with httpx.AsyncClient(timeout=4.0) as http_client:
                await http_client.post(webhook_url, json={"content": text, "text": text})
        except Exception as e:
            logger.warning(f"Failed to send webhook notification: {e}")

    async def record_contact_message(
        self,
        email: str,
        question: str,
        name: Optional[str] = None,
        client_ip: Optional[str] = None
    ) -> bool:
        """Stores the visitor's submitted question in Firestore and forwards alert to Brandon."""
        now = datetime.datetime.utcnow().isoformat() + "Z"
        client = self._get_client()

        contact_record = {
            "name": name or "Anonymous Visitor",
            "email": email,
            "question": question,
            "timestamp": now,
            "client_ip": client_ip or "unknown",
            "status": "pending_review",
        }

        # 1. Save to Firestore
        if client:
            try:
                doc_ref = client.collection(settings.FIRESTORE_COLLECTION_CONTACT).document()
                doc_ref.set(contact_record)
                logger.info(f"Recorded contact submission in Firestore: {email}")
            except Exception as e:
                logger.error(f"Failed to record contact message in Firestore: {e}")

        # 2. Forward to Webhook (Slack / Discord) if configured
        if settings.LEAD_NOTIFICATION_WEBHOOK_URL:
            webhook_text = (
                f"📬 **New Question Received from Portfolio Contact Form!**\n"
                f"• **From:** {name or 'Anonymous'} (<{email}>)\n"
                f"• **Question/Message:**\n> {question}\n\n"
                f"*Reply directly to {email}*"
            )
            try:
                async with httpx.AsyncClient(timeout=4.0) as http_client:
                    await http_client.post(
                        settings.LEAD_NOTIFICATION_WEBHOOK_URL,
                        json={"content": webhook_text, "text": webhook_text}
                    )
            except Exception as e:
                logger.warning(f"Failed to send webhook contact alert: {e}")

        # 3. Forward via SMTP if configured
        if settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASSWORD and settings.NOTIFICATION_EMAIL_TO:
            try:
                import smtplib
                from email.mime.text import MIMEText
                from email.mime.multipart import MIMEMultipart

                msg = MIMEMultipart()
                msg["Subject"] = f"[Portfolio Contact] New message from {name or email}"
                msg["From"] = settings.SMTP_FROM or settings.SMTP_USER
                msg["To"] = settings.NOTIFICATION_EMAIL_TO
                msg["Reply-To"] = email

                body = (
                    f"You received a new message from your portfolio contact form:\n\n"
                    f"Name: {name or 'Not provided'}\n"
                    f"Email: {email}\n"
                    f"Date: {now}\n\n"
                    f"Message:\n{question}\n\n"
                    f"---\nReply directly to this email to respond to {email}."
                )
                msg.attach(MIMEText(body, "plain"))

                with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                    server.starttls()
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                    server.send_message(msg)
                logger.info(f"Successfully sent contact email via SMTP to {settings.NOTIFICATION_EMAIL_TO}")
            except Exception as e:
                logger.warning(f"Failed to send SMTP contact email: {e}")

        # 4. Forward via Resend API if configured
        if settings.RESEND_API_KEY and settings.NOTIFICATION_EMAIL_TO:
            try:
                resend_payload = {
                    "from": settings.SMTP_FROM or "Portfolio Contact <onboarding@resend.dev>",
                    "to": [settings.NOTIFICATION_EMAIL_TO],
                    "reply_to": email,
                    "subject": f"[Portfolio Contact] New message from {name or email}",
                    "text": (
                        f"You received a new message from your portfolio contact form:\n\n"
                        f"Name: {name or 'Not provided'}\n"
                        f"Email: {email}\n"
                        f"Date: {now}\n\n"
                        f"Message:\n{question}\n\n"
                        f"---\nReply directly to this email to respond to {email}."
                    ),
                }
                async with httpx.AsyncClient(timeout=5.0) as http_client:
                    await http_client.post(
                        "https://api.resend.com/emails",
                        headers={"Authorization": f"Bearer {settings.RESEND_API_KEY}"},
                        json=resend_payload
                    )
                logger.info(f"Successfully sent contact email via Resend to {settings.NOTIFICATION_EMAIL_TO}")
            except Exception as e:
                logger.warning(f"Failed to send email via Resend API: {e}")

        # 5. Log high-visibility notification for server logs
        logger.info(
            f"📨 CONTACT MESSAGE FORWARDED: from='{email}' to='{settings.NOTIFICATION_EMAIL_TO or 'none'}': {question[:80]}"
        )
        return True


firestore_service = FirestoreLeadService()
