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
    # Clave de los dispositivos (sensores) que envían lecturas. Sin ella, la ingesta queda cerrada.
    device_api_key: SecretStr | None = None
    # Clave para resumir teléfonos y códigos de los avisos. Vacía = suscripciones cerradas.
    alerts_secret: SecretStr | None = None
    # Modo demostración: deja que quien se registra vea sus propios mensajes simulados (celular y
    # correo de mentira). Apagado por defecto: con canales reales, nadie lee mensajes ajenos.
    alerts_demo: bool = False
    # Tamaño máximo de un archivo a importar (el CSV real del SIGA pesa ~0,6 MB).
    max_upload_bytes: int = 5 * 1024 * 1024
    # Tamaño máximo del cuerpo de cualquier otro pedido (los JSON de la API pesan pocos bytes).
    max_request_bytes: int = 64 * 1024
    # Pedidos por minuto y por dirección. 0 desactiva el límite.
    rate_limit_per_minute: int = 120
    rate_limit_import_per_minute: int = 10
    # Registro e inicio de sesión: pocos pedidos por minuto y por dirección frenan la fuerza bruta.
    rate_limit_auth_per_minute: int = 10
    # Cuánto dura una sesión abierta.
    session_hours: int = 12
    # Si es false, nadie puede crear cuentas por la API (siguen las altas por línea de comandos).
    registration_open: bool = True

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
