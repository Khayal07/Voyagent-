from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://voyagent:voyagent@db:5432/voyagent"

    openai_api_key: str = ""
    openrouter_api_key: str = ""
    primary_provider: str = "openai"
    openai_model: str = "gpt-4o-mini"
    openrouter_model: str = "meta-llama/llama-3.3-70b-instruct:free"


settings = Settings()
