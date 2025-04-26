import enum
from pathlib import Path
from tempfile import gettempdir

from environs import Env
from pydantic_settings import BaseSettings, SettingsConfigDict
from yarl import URL

TEMP_DIR = Path(gettempdir())
env = Env()
env.read_env()


class LogLevel(str, enum.Enum):
    """Possible log levels."""

    NOTSET = "NOTSET"
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    FATAL = "FATAL"


class Settings(BaseSettings):
    """
    Application settings.

    These parameters can be configured
    with environment variables.
    """

    host: str = "127.0.0.1"
    port: int = 8000
    # quantity of workers for uvicorn
    workers_count: int = 1
    # Enable uvicorn reloading
    reload: bool = True

    TRACKER_TOKEN: str = env.str("TRACKER_TOKEN")
    TRACKER_ORG_ID: str = env.str("TRACKER_ORG_ID")

    # Current environment
    environment: str = "dev"

    log_level: LogLevel = LogLevel.INFO
    # Variables for the database
    db_host: str = env.str("DB_HOST")
    db_port: int = env.int("DB_PORT")
    db_user: str = env.str("DB_USER")
    db_pass: str = env.str("DB_PASS")
    db_base: str = env.str("DB_BASE")
    db_echo: bool = False

    webhook_secret_length: int = env.int("WEBHOOK_SECRET_LENGTH")
    backend_public_url: str = env.str("BACKEND_PUBLIC_URL")

    @property
    def db_url(self) -> URL:
        """
        Assemble database URL from settings.

        :return: database URL.
        """
        return URL.build(
            scheme="postgresql+asyncpg",
            host=self.db_host,
            port=self.db_port,
            user=self.db_user,
            password=self.db_pass,
            path=f"/{self.db_base}",
        )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="YAGIT_",
        env_file_encoding="utf-8",
    )


settings = Settings()
