from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"

class Settings(BaseSettings):
    ZAP_API_KEY: str = "changeme"
    ZAP_API_URL: str = "http://localhost:8080"
    ZAP_MIN_CONFIDENCE: str = "Medium"  # False positive reduction: Low, Medium, High

    XSSTRIKE_API_URL: str = "http://localhost:5000"
    SQLMAP_API_URL: str = "http://localhost:8775"

    DATABASE_URL: str
    FRONTEND_URL: str = "http://localhost:5173"

    # LLM provider selection: gemini | groq | claude
    LLM_PROVIDER: str = "gemini"

    GOOGLE_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"

    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-sonnet-4-6"

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
