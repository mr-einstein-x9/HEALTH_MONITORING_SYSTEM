import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Health Monitoring System API"
    TEST_DATABASE_URL: str = "sqlite:///./test.db"
    DATABASE_URL: str = "sqlite:///./health.db"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "supersecretkey1234567890")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"

settings = Settings()
