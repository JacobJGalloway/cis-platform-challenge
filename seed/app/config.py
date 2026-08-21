"""Settings, resolved from environment (portability-first).

Every external dependency is chosen by env var so the platform stays vendor-portable. Dev defaults
use local backends; production overrides via env / Key Vault.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CIS_", env_file=".env", extra="ignore")

    # postgresql+asyncpg://user:pass@host:6432/cis_platform  (PgBouncer port in prod)
    database_url: str = "postgresql+asyncpg://cis:cis@localhost:5432/cis_platform"
    environment: str = "local"


settings = Settings()
