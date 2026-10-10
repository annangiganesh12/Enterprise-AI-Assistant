
from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):

    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    GOOGLE_API_KEY: str
    JIRA_URL: str
    JIRA_API_TOKEN: str
    GOOGLE_DRIVE_URL: str
    GOOGLE_ACCESS_TOKEN: str
    TAVILY_API_KEY: str
    LANGSMITH_API_KEY: str | None = None
    LANGSMITH_PROJECT: str = "Enterprise-AI-Assistant"
    MAX_ADMINS: int = 5
    OPENROUTER_API_KEY: str


    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

settings = Settings()

# Inject LangSmith environment variables for observability immediately upon settings initialization
if settings.LANGSMITH_API_KEY:
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
    os.environ["LANGCHAIN_API_KEY"] = settings.LANGSMITH_API_KEY
    os.environ["LANGCHAIN_PROJECT"] = settings.LANGSMITH_PROJECT

    