from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env')

    ACCESS_TOKEN_EXP_MINS: int = 15
    SECRET_KEY: str
    JWT_ALGORITHM: str = 'HS256'
    DUMMY_PASS: str
    DB_USERNAME: str = "postgres"
    DB_PASSWORD: str = "postgres"
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "gamelib"

    def _build_db_url(self, driver: str) -> str:
        return f'postgresql+{driver}://{self.DB_USERNAME}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}'

    @property
    def sync_database_url(self) -> str:
        return self._build_db_url('psycopg')

    @property
    def async_database_url(self) -> str:
        return self._build_db_url('asyncpg')

settings = Settings()
