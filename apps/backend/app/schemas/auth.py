from datetime import UTC, datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.alerts import normalize_email
from app.domain.auth import MAX_PASSWORD, Role, validate_password


class RegisterIn(BaseModel):
    """Registro de una cuenta. El rol no se puede elegir: siempre nace como ciudadano."""

    model_config = ConfigDict(extra="forbid")

    email: str
    password: Annotated[str, Field(max_length=MAX_PASSWORD)]
    display_name: Annotated[str | None, Field(max_length=80)] = None

    @field_validator("email")
    @classmethod
    def _correo(cls, value: str) -> str:
        return normalize_email(value)

    @field_validator("display_name")
    @classmethod
    def _nombre(cls, value: str | None) -> str | None:
        return value.strip() or None if value else None

    def check_password(self) -> None:
        validate_password(self.password, self.email)


class LoginIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: Annotated[str, Field(max_length=254)]
    password: Annotated[str, Field(max_length=MAX_PASSWORD)]


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    display_name: str | None
    role: Role
    is_active: bool
    created_at: datetime
    last_login_at: datetime | None

    @field_validator("created_at", "last_login_at")
    @classmethod
    def _en_utc(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            return value.replace(tzinfo=UTC)  # SQLite devuelve la hora sin zona; se guarda en UTC
        return value


class SessionOut(BaseModel):
    token: str
    expires_at: datetime
    user: UserOut


class UserList(BaseModel):
    items: list[UserOut]
    total: int


class UserPatch(BaseModel):
    """Lo único que se puede cambiar de una cuenta ajena: su rol y si está activa."""

    model_config = ConfigDict(extra="forbid")

    role: Role | None = None
    is_active: bool | None = None
