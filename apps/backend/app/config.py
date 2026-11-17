"""Configuración de la aplicación, leída de variables de entorno (ver .env.example)."""

from datetime import date
from functools import lru_cache
from typing import Annotated, Literal

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Se busca primero en apps/backend y después en la raíz del repositorio.
        env_file=(".env", "../../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: Literal["development", "test", "production"] = "development"
    database_url: str = "sqlite:///./pluvifor.db"
    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:5173"]
    data_cutoff_date: date = date(2026, 10, 31)
    admin_api_key: SecretStr | None = None

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            value = [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("cors_origins")
    @classmethod
    def _no_wildcard(cls, value: list[str]) -> list[str]:
        if "*" in value:
            raise ValueError('CORS_ORIGINS no puede incluir "*": listar los orígenes permitidos.')
        return value

    @property
    def docs_enabled(self) -> bool:
        """La documentación interactiva (/docs) se apaga en producción."""
        return self.app_env != "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
