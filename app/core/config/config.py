from typing import List, Optional

from pydantic import (
    AnyHttpUrl,
    EmailStr,
    Field,
    PostgresDsn,
    field_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict


class DBSettings(BaseSettings):
    POSTGRES_SERVER: Optional[str] = None
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_DB: Optional[str] = None
    INSTANCE_CONNECTION_NAME: Optional[str] = None

    SQLALCHEMY_DATABASE_URI: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    @field_validator("SQLALCHEMY_DATABASE_URI", mode="before")
    @classmethod
    def assemble_db_connection(cls, value, info):
        if isinstance(value, str) and value:
            return value

        user = info.data.get("POSTGRES_USER")
        password = info.data.get("POSTGRES_PASSWORD")
        database = info.data.get("POSTGRES_DB")
        instance_connection_name = info.data.get("INSTANCE_CONNECTION_NAME")

        if not all([user, password, database]):
            return None

        # Cloud Run + Cloud SQL Unix socket
        if instance_connection_name:
            return (
                f"postgresql+psycopg2://"
                f"{user}:{password}@/{database}"
                f"?host=/cloudsql/{instance_connection_name}"
            )

        # Local/development connection
        server = info.data.get("POSTGRES_SERVER")

        if not server:
            return None

        return (
            f"postgresql+psycopg2://"
            f"{user}:{password}@{server}/{database}"
        )

class SMTPSettings(BaseSettings):
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = None
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


class AzureSettings(BaseSettings):
    AZURE_BLOB_SAS_TOKEN: Optional[str] = None
    AZURE_BLOB_CONNECTION_STRING: Optional[str] = None
    AZURE_BASE_URL: Optional[str] = None
    BASE_URL: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


class EmailSettings(BaseSettings):
    EMAILS_FROM_EMAIL: Optional[EmailStr] = None
    EMAILS_FROM_NAME: Optional[str] = None

    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int = 48
    EMAIL_TEMPLATES_DIR: str = "/app/app/email-templates/build"

    EMAIL_TEST_USER: Optional[EmailStr] = None
    USERS_OPEN_REGISTRATION: bool = False
    PROJECT_NAME: str = "aaralia"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    @field_validator("EMAILS_FROM_NAME")
    @classmethod
    def get_project_name(cls, value: Optional[str]) -> str:
        return value or "aaralia"


class DefaultSettings(BaseSettings):
    FIRST_SUPERUSER: Optional[EmailStr] = None
    FIRST_SUPERUSER_PASSWORD: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


class APISettings(BaseSettings):
    API_V1_STR: str = "/api/v1"

    SECRET_KEY: str = Field(
        ...,
        description="JWT signing secret",
    )

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 86400

    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    ALGORITHM: str = "HS256"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


class SentrySettings(BaseSettings):
    SENTRY_DSN: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


class Settings:
    def __init__(self):
        self.SMTP = SMTPSettings()
        self.DB = DBSettings()
        self.EMAIL = EmailSettings()
        self.AZURE = AzureSettings()
        self.API = APISettings()
        self.DEFAULTS = DefaultSettings()
        self.SENTRY = SentrySettings()


AppSettings = Settings()