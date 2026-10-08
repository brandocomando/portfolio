"""Application Configuration Settings.

Uses Pydantic v2 BaseSettings to load environment variables from Cloud Run or local .env.
"""

from typing import List, Optional
from pathlib import Path
import logging
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


def _fetch_gcp_secret(secret_id: str, project_id: Optional[str] = None) -> Optional[str]:
    """Attempt to retrieve secret payload from GCP Secret Manager.

    Returns None gracefully if Secret Manager client is unavailable, unauthenticated,
    or the secret does not exist, allowing seamless fallback to .env or environment variables.
    """
    if not secret_id:
        return None
    try:
        import os
        from google.cloud import secretmanager

        proj = project_id or os.getenv("GCP_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT")
        if not proj:
            try:
                import google.auth
                _, default_proj = google.auth.default()
                proj = default_proj
            except Exception:
                pass

        if not proj:
            return None

        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{proj}/secrets/{secret_id}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        val = response.payload.data.decode("UTF-8").strip()
        return val if val else None
    except Exception as exc:
        logger.debug("GCP Secret Manager lookup skipped/failed: %s", exc)
        return None


class Settings(BaseSettings):
    APP_NAME: str = "Brandon Foster AI Portfolio Service"
    ENV: str = "development"
    DEBUG: bool = False
    PORT: int = 8080
    HOST: str = "0.0.0.0"

    # Domain & Client Verification
    CUSTOM_DOMAIN: str = "www.brandonfoster.dev"
    CLIENT_VERIFICATION_ENABLED: bool = True
    CLIENT_VERIFICATION_HEADER: str = "x-portfolio-client"
    CLIENT_VERIFICATION_SECRET: str = "portfolio-client-v1"

    # CORS Allowed Origins
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
        "https://portfolio-510722.web.app",
        "https://portfolio-510722.firebaseapp.com",
        "https://brandonfoster.dev",
        "https://www.brandonfoster.dev",
    ]

    # AI Model Settings
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-flash-latest"
    MAX_TOKENS: int = 1024
    TEMPERATURE: float = 0.2

    # Rate Limiting (Token Bucket)
    ANON_DAILY_LIMIT: int = 5
    AUTH_DAILY_LIMIT: int = 10
    RATE_LIMIT_WINDOW_SECONDS: int = 86400  # 24 hours

    # GCP & Firebase
    GCP_PROJECT_ID: Optional[str] = None
    FIREBASE_PROJECT_ID: Optional[str] = None
    FIRESTORE_COLLECTION_LEADS: str = "portfolio_leads"
    FIRESTORE_COLLECTION_CONVERSATIONS: str = "portfolio_conversations"

    NOTIFICATION_EMAIL_TO: Optional[str] = None
    NOTIFICATION_EMAIL_SECRET_ID: Optional[str] = "notification-email"
    SMTP_PASSWORD_SECRET_ID: Optional[str] = "smtp-password"
    LEAD_NOTIFICATION_WEBHOOK_URL: Optional[str] = None
    FIRESTORE_COLLECTION_CONTACT: str = "portfolio_contact_messages"
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM: Optional[str] = None
    RESEND_API_KEY: Optional[str] = None

    # Storage Paths
    GOLD_INDEX_PATH: Path = (
        Path(__file__).resolve().parent.parent.parent.parent / "mlops" / "data" / "gold" / "gold_index.json"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @model_validator(mode="after")
    def resolve_secrets_and_domain(self) -> "Settings":
        if not self.NOTIFICATION_EMAIL_TO and self.NOTIFICATION_EMAIL_SECRET_ID:
            secret_val = _fetch_gcp_secret(
                secret_id=self.NOTIFICATION_EMAIL_SECRET_ID,
                project_id=self.GCP_PROJECT_ID
            )
            if secret_val:
                self.NOTIFICATION_EMAIL_TO = secret_val

        if not self.SMTP_PASSWORD and self.SMTP_PASSWORD_SECRET_ID:
            secret_val = _fetch_gcp_secret(
                secret_id=self.SMTP_PASSWORD_SECRET_ID,
                project_id=self.GCP_PROJECT_ID
            )
            if secret_val:
                self.SMTP_PASSWORD = secret_val

        if not self.SMTP_USER and self.NOTIFICATION_EMAIL_TO:
            self.SMTP_USER = self.NOTIFICATION_EMAIL_TO

        if not self.SMTP_HOST and self.SMTP_USER and "@gmail.com" in self.SMTP_USER.lower():
            self.SMTP_HOST = "smtp.gmail.com"

        # Dynamically ensure CUSTOM_DOMAIN origins are added to CORS_ORIGINS
        if self.CUSTOM_DOMAIN:
            cleaned_domain = self.CUSTOM_DOMAIN.strip().lower().removeprefix("http://").removeprefix("https://")
            for origin in [f"https://{cleaned_domain}", f"https://www.{cleaned_domain}"]:
                if origin not in self.CORS_ORIGINS:
                    self.CORS_ORIGINS.append(origin)

        return self


settings = Settings()

