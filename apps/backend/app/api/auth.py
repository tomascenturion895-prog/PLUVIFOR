from typing import Annotated

from fastapi import APIRouter, Depends, Header, Path, Query

from app.api.deps import bearer_token, get_auth_service, require_role, require_user
from app.domain.auth import Role
from app.models import User
from app.schemas.auth import LoginIn, RegisterIn, SessionOut, UserList, UserOut, UserPatch
from app.schemas.ids import MAX_ID
from app.services.auth import AuthService

router = APIRouter(prefix="/api/auth", tags=["cuentas"])
users_router = APIRouter(prefix="/api/users", tags=["cuentas (administración)"])

Service = Annotated[AuthService, Depends(get_auth_service)]


@router.post(
    "/register",
    response_model=UserOut,
    status_code=201,
    summary="Crear una cuenta de ciudadano",
)
def register(data: RegisterIn, service: Service) -> UserOut:
    """El rol no se elige: toda cuenta nueva es de ciudadano. Operadores y administradores los
    asigna un administrador (o el primero se crea por línea de comandos)."""
    return UserOut.model_validate(service.register(data))


@router.post("/login", response_model=SessionOut, summary="Iniciar sesión")
def login(data: LoginIn, service: Service) -> SessionOut:
    return service.login(data)


@router.post("/logout", status_code=204, summary="Cerrar la sesión actual")
def logout(
    service: Service,
    authorization: Annotated[str | None, Header()] = None,
) -> None:
    token = bearer_token(authorization)
    if token:
        service.logout(token)


@router.get("/me", response_model=UserOut, summary="La cuenta de la sesión actual")
def me(user: Annotated[User, Depends(require_user)]) -> UserOut:
    return UserOut.model_validate(user)


@users_router.get("", response_model=UserList, summary="Cuentas (solo administradores)")
def list_users(
    service: Service,
    _admin: Annotated[User, Depends(require_role(Role.ADMINISTRADOR))],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> UserList:
    items, total = service.list_users(limit, offset)
    return UserList(items=[UserOut.model_validate(u) for u in items], total=total)


@users_router.patch(
    "/{user_id}",
    response_model=UserOut,
    summary="Cambiar el rol o activar o desactivar una cuenta (solo administradores)",
)
def update_user(
    user_id: Annotated[int, Path(ge=1, le=MAX_ID)],
    data: UserPatch,
    service: Service,
    admin: Annotated[User, Depends(require_role(Role.ADMINISTRADOR))],
) -> UserOut:
    return UserOut.model_validate(service.update_user(admin, user_id, data))
