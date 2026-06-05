from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    anthropic_api_key: str = ""
    # OpenAI-compatible local model fallback (Ollama, LM Studio, etc.)
    openai_base_url: str   = "http://localhost:11434/v1"
    openai_api_key: str    = "local"  # many local servers ignore this
    openai_model: str      = "llama3"
    teams_webhook: str     = ""
    jira_url: str          = ""
    jira_token: str        = ""
    github_token: str      = ""
    wiki_repo: str         = ""
    database_url: str      = "sqlite:///./tickets.db"

    class Config:
        env_file = ".env"


settings = Settings()
