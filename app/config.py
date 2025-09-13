from __future__ import annotations

from functools import lru_cache
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="allow")

    app_name: str = Field(default="TaskManagerAgent")
    app_env: str = Field(default="development")
    app_host: str = Field(default="127.0.0.1")
    app_port: int = Field(default=8000)
    secret_key: str = Field(alias="APP_SECRET_KEY")

    database_url: str = Field(alias="DATABASE_URL")
    sync_database_url: str = Field(alias="SYNC_DATABASE_URL")

    default_tz: str = Field(default="America/New_York", alias="DEFAULT_TZ")
    work_hours_start: str = Field(default="09:00", alias="WORK_HOURS_START")
    work_hours_end: str = Field(default="17:00", alias="WORK_HOURS_END")

    openai_api_key: str = Field(alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o", alias="OPENAI_MODEL")
    openai_max_output_tokens: int = Field(default=512, alias="OPENAI_MAX_OUTPUT_TOKENS")
    openai_temperature: float = Field(default=0.3, alias="OPENAI_TEMPERATURE")
    openai_top_p: float = Field(default=1.0, alias="OPENAI_TOP_P")

    n8n_webhook_url: str = Field(alias="N8N_WEBHOOK_URL")
    n8n_webhook_secret: str = Field(alias="N8N_WEBHOOK_SECRET")

    initial_admin_email: str = Field(alias="INITIAL_ADMIN_EMAIL")
    initial_admin_password: str = Field(alias="INITIAL_ADMIN_PASSWORD")

    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    dry_run: bool = Field(default=False, alias="DRY_RUN")


class LLMConfig(BaseModel):
    model: str
    temperature: float
    top_p: float
    max_output_tokens: int


@lru_cache()
def get_settings() -> Settings:
    return Settings()  # type: ignore[arg-type]


def get_llm_config() -> LLMConfig:
    s = get_settings()
    return LLMConfig(
        model=s.openai_model,
        temperature=s.openai_temperature,
        top_p=s.openai_top_p,
        max_output_tokens=s.openai_max_output_tokens,
    )

