from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / 'db.sqlite3'

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env')

    ACCESS_TOKEN_EXP_MINS: int = 15
    SECRET_KEY: str
    JWT_ALGORITHM: str = 'HS256'
    DUMMY_PASS: str
    DB_URL: str = f'sqlite:///{DB_PATH}'


settings = Settings()
