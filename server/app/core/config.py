from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    ZAP_API_KEY: str = "changeme"
    ZAP_API_URL: str = "http://localhost:8080"
    ZAP_MIN_CONFIDENCE: str = "Medium"  # False positive reduction: Low, Medium, High
    DATABASE_URL: str
    GOOGLE_API_KEY: str = ""
    FRONTEND_URL: str = "http://localhost:5173"  # Default Vue.js local dev port

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
