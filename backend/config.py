from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    anthropic_api_key: str = ""
    teams_webhook: str     = ""
    jira_url: str          = ""
    jira_token: str        = ""
    github_token: str      = ""
    wiki_repo: str         = ""
    database_url: str      = "sqlite:///./tickets.db"

    class Config:
        env_file = ".env"


settings = Settings()
