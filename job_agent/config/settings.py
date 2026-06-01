from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", frozen=True)

    # LLM providers
    openai_api_key: str = Field(default="")
    anthropic_api_key: str = Field(default="")
    google_api_key: str = Field(default="")
    groq_api_key: str = Field(default="")

    # LinkedIn OAuth2
    linkedin_client_id: str = Field(default="")
    linkedin_client_secret: str = Field(default="")
    linkedin_redirect_uri: str = Field(default="http://localhost:8000/auth/linkedin/callback")

    # Gmail OAuth2
    gmail_client_id: str = Field(default="")
    gmail_client_secret: str = Field(default="")
    gmail_refresh_token: str = Field(default="")

    # Captcha
    twocaptcha_api_key: str = Field(default="")
    capsolver_api_key: str = Field(default="")

    # Proxies
    proxy_http: str = Field(default="")
    proxy_username: str = Field(default="")
    proxy_password: str = Field(default="")

    # Notifications
    telegram_bot_token: str = Field(default="")
    telegram_chat_id: str = Field(default="")

    # Observability
    langsmith_api_key: str = Field(default="")
    langsmith_project: str = Field(default="job-agent")

    # Search
    tavily_api_key: str = Field(default="")
    serpapi_api_key: str = Field(default="")

    # DB / Queue
    database_url: str = Field(...)
    redis_url: str = Field(default="redis://localhost:6379/0")

    # App
    app_api_key: str = Field(...)
    secret_key: str = Field(...)
