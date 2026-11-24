from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_PROJECT_ENV = Path(__file__).resolve().parents[3] / ".env"


def _odbc_value(value: str) -> str:
    """Return an ODBC attribute value, brace-quoting it only when it must be quoted.

    The CONNX driver passes braces through literally, so quoting every value makes
    an ordinary password fail to log in. Values containing ';', '{', '}' or
    surrounding spaces are quoted per the ODBC spec; confirm such credentials
    work with your CONNX driver version.
    """
    if any(ch in value for ch in ";{}") or value != value.strip():
        return "{" + value.replace("}", "}}") + "}"
    return value


class Settings(BaseSettings):
    """Runtime configuration, sourced exclusively from environment/.env."""

    model_config = SettingsConfigDict(env_file=(str(_PROJECT_ENV), ".env"), env_prefix="CONNX_RMS_", extra="ignore")

    dsn: str = "CONNX_RMS"
    table: str = "RMS.dbo.customers_rms"
    user: str | None = None
    password: str | None = None
    extra_connection_string: str | None = None
    connect_timeout_seconds: int = 15
    query_timeout_seconds: int = 30
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    log_level: str = "INFO"

    def connection_string(self) -> str:
        parts = [f"DSN={self.dsn}"]
        if self.user:
            parts.append(f"UID={_odbc_value(self.user)}")
        if self.password:
            parts.append(f"PWD={_odbc_value(self.password)}")
        if self.extra_connection_string:
            parts.append(self.extra_connection_string.strip(";"))
        return ";".join(parts) + ";"


@lru_cache
def get_settings() -> Settings:
    return Settings()
