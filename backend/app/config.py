from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://voyagent:voyagent@db:5432/voyagent"

    openai_api_key: str = ""
    openrouter_api_key: str = ""
    geoapify_api_key: str = ""
    primary_provider: str = "openai"
    openai_model: str = "gpt-4o-mini"
    openrouter_model: str = "openrouter/free"

    jwt_secret: str = "dev-secret-change-me-in-production-0000"
    jwt_expire_days: int = 7


settings = Settings()
