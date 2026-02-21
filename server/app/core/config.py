from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    ZAP_API_KEY: str = "changeme"
    ZAP_API_URL: str = "http://localhost:8080"
    DATABASE_URL: str
    FRONTEND_URL: str = "http://localhost:5173"  # Default Vue.js local dev port

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
