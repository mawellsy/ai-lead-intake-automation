"""Central application configuration.

Secrets and deployment-specific settings are read from environment variables
rather than being committed to source control.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    app_name: str = "ai-lead-intake-automation"
    database_url: str = "sqlite:///./lead_automation.db"

    openai_api_key: str | None = None
    openai_model: str | None = None

    n8n_webhook_secret: str | None = None
    staff_notification_webhook_url: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
