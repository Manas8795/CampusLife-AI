import os
import sys
from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "CampusLife AI"
    API_V1_STR: str = "/api"

    # --- Core Security ---
    # Must be set via environment variable or .env file. Never hardcode.
    SECRET_KEY: str = os.getenv("SECRET_KEY", "campuslife-super-secret-key-for-development")

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./campuslife.db")

    # --- Module 7 & 8: LLM Architecture ---
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "local")  # "local" | "ollama" | "openai" | "gemini"
    LOCAL_LLM_URL: str = os.getenv("LOCAL_LLM_URL", "http://127.0.0.1:11434")
    LOCAL_LLM_MODEL: str = os.getenv("LOCAL_LLM_MODEL", "llama3.2:1b")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    STUDENT_PERSONA: str = os.getenv("STUDENT_PERSONA", "EMPATHETIC_MENTOR")

    # --- Twilio Telephony Credentials ---
    # Set these via environment variables or a .env file (NEVER commit real values to git).
    # Copy .env.example to .env and fill in your credentials.
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_PHONE_NUMBER: str = os.getenv("TWILIO_PHONE_NUMBER", "")

    # --- Telegram Voice Telephony Bot ---
    # Set these via environment variables or a .env file.
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")
    TELEGRAM_API_BASE: str = os.getenv("TELEGRAM_API_BASE", "https://api.telegram.org")
    TELEGRAM_PROXY: str = os.getenv("TELEGRAM_PROXY", "")

    model_config = ConfigDict(case_sensitive=True)


settings = Settings()

# ---------------------------------------------------------------------------
# Startup Validation (OWASP A02: Cryptographic Failures prevention)
# Warn — but do not crash — if sensitive credentials are missing.
# Telephony features will gracefully degrade without them.
# ---------------------------------------------------------------------------
_MISSING_CREDS = []
if not settings.TWILIO_ACCOUNT_SID:
    _MISSING_CREDS.append("TWILIO_ACCOUNT_SID")
if not settings.TWILIO_AUTH_TOKEN:
    _MISSING_CREDS.append("TWILIO_AUTH_TOKEN")
if not settings.TELEGRAM_BOT_TOKEN:
    _MISSING_CREDS.append("TELEGRAM_BOT_TOKEN")

if _MISSING_CREDS:
    import logging
    _cfg_logger = logging.getLogger("campuslife.config")
    _cfg_logger.warning(
        "missing_credentials_warning",
        extra={
            "missing": _MISSING_CREDS,
            "hint": "Copy .env.example to .env and fill in your credentials. "
                    "Telephony (Twilio/Telegram) features will be disabled until configured.",
        },
    )
