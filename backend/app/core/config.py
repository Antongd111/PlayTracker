from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    DATABASE_URL: str
    ALGORITHM: str
    RAWG_API_KEY: str

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()