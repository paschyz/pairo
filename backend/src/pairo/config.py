from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    debug: bool = False
    database_url: str = "sqlite:///./pairo.db"
    github_app_id: int = 0
    github_private_key_path: str = "./pairo.private-key.pem"
    github_private_key: str = ""
    github_webhook_secret: str = ""
    llm_provider: str = "fake"
    gemini_api_key: str = ""
    llm_model_default: str = ""
    llm_model_large: str = ""
    llm_rpm_limit: int = 15
    daily_review_quota: int = 50
    dashboard_origin: str = "http://localhost:3000"
    smee_url: str = ""
    llm_cache_ttl_days: int = 30


settings = Settings()
