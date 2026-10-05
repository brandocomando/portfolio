"""Application Configuration Settings.

Uses Pydantic v2 BaseSettings to load environment variables from Cloud Run or local .env.
"""

from typing import List, Optional
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Brandon Foster AI Portfolio Service"
    ENV: str = "development"
    DEBUG: bool = False
    PORT: int = 8080
    HOST: str = "0.0.0.0"

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "https://*.web.app",
        "https://*.firebaseapp.com",
        "*"
    ]

    # AI Model Settings
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.0-flash"
    MAX_TOKENS: int = 1024
    TEMPERATURE: float = 0.2

    # Rate Limiting (Token Bucket)
    ANON_DAILY_LIMIT: int = 10
    AUTH_DAILY_LIMIT: int = 30
    RATE_LIMIT_WINDOW_SECONDS: int = 86400  # 24 hours

    # GCP & Firebase
    GCP_PROJECT_ID: Optional[str] = None
    FIREBASE_PROJECT_ID: Optional[str] = None
    FIRESTORE_COLLECTION_LEADS: str = "portfolio_leads"
    FIRESTORE_COLLECTION_CONVERSATIONS: str = "portfolio_conversations"

    # Lead Alerts (Optional Discord / Slack / Telegram Webhook)
    LEAD_NOTIFICATION_WEBHOOK_URL: Optional[str] = None

    # Storage Paths
    GOLD_INDEX_PATH: Path = (
        Path(__file__).resolve().parent.parent.parent.parent / "mlops" / "data" / "gold" / "gold_index.json"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
