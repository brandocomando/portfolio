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


firestore_service = FirestoreLeadService()
