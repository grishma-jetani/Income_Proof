# from pydantic_settings import BaseSettings


# class Settings(BaseSettings):
#     DATABASE_URL: str
#     GEMINI_API_KEY: str = ""
#     UPLOAD_DIR: str = "uploads"
#     SUPABASE_JWT_SECRET: str = ""

#     class Config:
#         env_file = ".env"


# settings = Settings()
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    GEMINI_API_KEY: str = ""
    UPLOAD_DIR: str = "uploads"
    SUPABASE_URL: str = ""  # Replaced the secret with the URL
    REDIS_URL: str = "redis://localhost:6379/0"

    class Config:
        env_file = ".env"

settings = Settings()
