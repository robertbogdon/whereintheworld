"""Application configuration via environment variables.

All configuration is sourced from environment variables (prefixed with WITW_).
No secrets or environment-specific values are hardcoded.
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    db_host: str = "localhost"
    db_port: int = 5432
    db_user: str = "witw"
    db_password: str = ""
    db_name: str = "whereintheworld"

    # Auth
    api_key: str = ""

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    model_config = {
        "env_prefix": "WITW_",
        "case_sensitive": False,
    }


settings = Settings()
