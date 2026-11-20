"""Registro, inicio de sesión y gestión de cuentas.

Reglas: el registro público solo crea ciudadanos; los errores de inicio de sesión no dicen si el
correo existe; tras 5 intentos fallidos la cuenta se bloquea 15 minutos; los tokens se guardan
resumidos y vencen; desactivar una cuenta cierra todas sus sesiones.
"""

from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from app.domain.auth import (
    DUMMY_HASH,
    LOCK_MINUTES,
    MAX_FAILED_ATTEMPTS,
    Role,
    hash_password,
    new_session_token,
    token_digest,
    validate_password,
    verify_password,
)
from app.errors import ApiError
from app.models import AuthSession, User
from app.repositories.users import SqlUserRepository
from app.schemas.auth import LoginIn, RegisterIn, SessionOut, UserOut, UserPatch

Now = Callable[[], datetime]


def _aware(value: datetime) -> datetime:
    """SQLite devuelve las horas sin zona; se guardan siempre en UTC."""
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value


class AuthService:
    def __init__(
        self,
        repository: SqlUserRepository,
        session_hours: int,
        registration_open: bool = True,
        now: Now = lambda: datetime.now(UTC),
    ):
        self._repository = repository
        self._session_hours = session_hours
        self._registration_open = registration_open
        self._now = now

    # --- registro y sesión -----------------------------------------------------------------

    def register(self, data: RegisterIn) -> User:
        if not self._registration_open:
            raise ApiError(403, "forbidden", "El registro de cuentas está cerrado.")
        try:
            data.check_password()
        except ValueError as error:
            raise ApiError(422, "invalid_password", str(error)) from error
        if self._repository.by_email(data.email) is not None:
            raise ApiError(409, "email_taken", "Ya hay una cuenta con ese correo.")
        user = self._repository.add(
            User(
                email=data.email,
                password_hash=hash_password(data.password),
                display_name=data.display_name,
                role=Role.CIUDADANO,  # el rol nunca lo elige quien se registra
            )
        )
        self._repository.commit()
        return user

    def create_user(self, email: str, password: str, role: Role) -> User:
        """Alta desde la línea de comandos (por ejemplo, el primer administrador)."""
        validate_password(password, email)
        if self._repository.by_email(email) is not None:
            raise ApiError(409, "email_taken", "Ya hay una cuenta con ese correo.")
        user = self._repository.add(
            User(email=email, password_hash=hash_password(password), role=role)
        )
        self._repository.commit()
        return user

    def login(self, data: LoginIn) -> SessionOut:
        invalid = ApiError(401, "invalid_credentials", "Correo o contraseña incorrectos.")
        user = self._repository.by_email(data.email.strip().lower())
        if user is None:
            verify_password(data.password, DUMMY_HASH)  # tarda lo mismo que con un correo real
            raise invalid
        now = self._now()
        if user.locked_until is not None and _aware(user.locked_until) > now:
            raise ApiError(
                429,
                "account_locked",
                f"Demasiados intentos: probá de nuevo en {LOCK_MINUTES} minutos.",
            )
        if not verify_password(data.password, user.password_hash) or not user.is_active:
            if user.is_active:
                user.failed_attempts += 1
                if user.failed_attempts >= MAX_FAILED_ATTEMPTS:
                    user.locked_until = now + timedelta(minutes=LOCK_MINUTES)
                    user.failed_attempts = 0
                self._repository.commit()
            raise invalid
        user.failed_attempts = 0
        user.locked_until = None
        user.last_login_at = now
        token = new_session_token()
        expires = now + timedelta(hours=self._session_hours)
        self._repository.add_session(
            AuthSession(user_id=user.id, token_hash=token_digest(token), expires_at=expires)
        )
        self._repository.commit()
        return SessionOut(token=token, expires_at=expires, user=UserOut.model_validate(user))

    def authenticate(self, token: str) -> User | None:
        """La cuenta de un token vigente, o None (vencido, revocado, desconocido o inactiva)."""
        found = self._repository.session_by_hash(token_digest(token))
        if found is None:
            return None
        auth_session, user = found
        if auth_session.revoked_at is not None or _aware(auth_session.expires_at) <= self._now():
            return None
        return user if user.is_active else None

    def logout(self, token: str) -> None:
        found = self._repository.session_by_hash(token_digest(token))
        if found is not None and found[0].revoked_at is None:
            found[0].revoked_at = self._now()
            self._repository.commit()

    # --- gestión de cuentas (solo administradores) -----------------------------------------

    def list_users(self, limit: int, offset: int) -> tuple[list[User], int]:
        return self._repository.list_users(limit, offset)

    def update_user(self, actor: User, user_id: int, patch: UserPatch) -> User:
        target = self._repository.get(user_id)
        if target is None:
            raise ApiError(404, "user_not_found", "No existe esa cuenta.")
        if target.id == actor.id:
            # Evita quedarse sin administradores por un error propio.
            raise ApiError(
                409, "cannot_modify_self", "No podés cambiar tu propio rol ni desactivarte."
            )
        if patch.role is not None:
            target.role = patch.role
        if patch.is_active is not None:
            target.is_active = patch.is_active
            if not patch.is_active:
                self._repository.revoke_sessions(target.id, self._now())
        if patch.role is not None and patch.role != Role.ADMINISTRADOR:
            self._repository.revoke_sessions(target.id, self._now())  # el permiso cambió: reingresa
        self._repository.commit()
        return target
