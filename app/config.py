import os
from pydantic_settings import BaseSettings
from typing import List, Optional
from functools import lru_cache

class Settings(BaseSettings):
    # App settings
    APP_NAME: str = "Microsoft Graph Email Service"
    DEBUG: bool = True
    
    # MongoDB settings
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "email_service_db")
    
    # Microsoft Graph API settings
    TENANT_ID: str = os.getenv("TENANT_ID", "")
    CLIENT_ID: str = os.getenv("CLIENT_ID", "")
    CLIENT_SECRET: str = os.getenv("CLIENT_SECRET", "")
    USER_EMAIL: str = os.getenv("USER_EMAIL", "")
    REDIRECT_URI: str = os.getenv("REDIRECT_URI", "http://localhost:8000/callback")
    GRAPH_API_VERSION: str = os.getenv("GRAPH_API_VERSION", "v1.0")
    GRAPH_API_ENDPOINT: str = os.getenv("GRAPH_API_ENDPOINT", "https://graph.microsoft.com")
    
    # Scheduler settings
    EMAIL_FETCH_INTERVAL_MINUTES: int = int(os.getenv("EMAIL_FETCH_INTERVAL_MINUTES", "60"))
    EMAIL_FETCH_HOURS: int = int(os.getenv("EMAIL_FETCH_HOURS", "24"))
    EMAIL_BATCH_SIZE: int = int(os.getenv("EMAIL_BATCH_SIZE", "50"))
    EMAIL_MAX_RETRIES: int = int(os.getenv("EMAIL_MAX_RETRIES", "3"))
    EMAIL_RETRIEVE_ATTACHMENTS: bool = os.getenv("EMAIL_RETRIEVE_ATTACHMENTS", "True").lower() == "true"
    EMAIL_RETRIEVE_BODY: bool = os.getenv("EMAIL_RETRIEVE_BODY", "True").lower() == "true"
    
    # CORS settings
    CORS_ORIGINS: List[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    # Microsoft Graph API authority URL
    @property
    def AUTHORITY(self) -> str:
        return f"https://login.microsoftonline.com/{self.TENANT_ID}"
    
    
    # Microsoft Graph API scopes
    @property
    def SCOPE(self) -> List[str]:
        return ["https://graph.microsoft.com/.default"]

    
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    """Get application settings with caching for efficiency"""
    return Settings()