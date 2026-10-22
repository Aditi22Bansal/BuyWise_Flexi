from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # API
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "BuyWise"
    VERSION: str = "1.0.0"

    # CORS
    BACKEND_CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:3001"]

    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/buywise"

    # Security
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    # Workflow
    WORKFLOW_TIMEOUT_SECONDS: int = 300
    MAX_NEGOTIATION_ROUNDS: int = 3

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()