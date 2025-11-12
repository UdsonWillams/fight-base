from fastapi import Depends
from fastapi.security import (  # substitui OAuth2PasswordBearer
    HTTPAuthorizationCredentials,
    HTTPBearer,
)

from app.database.repositories.user import UserRepository
from app.database.unit_of_work import UnitOfWorkConnection, get_uow
from app.exceptions.exceptions import UnauthorizedError
from app.schemas.auth import AuthenticatedUser, RoleEnum
from app.services.auth.authentication import AuthService, get_auth_service

# Explicação: OAuth2PasswordBearer pede email/senha no Swagger para trocar por token.
# Como o fluxo aqui já expõe um endpoint JSON de login, usamos HTTPBearer para apenas aceitar "Authorization: Bearer <token>".
http_bearer = HTTPBearer()


async def get_current_user(
    token: HTTPAuthorizationCredentials = Depends(http_bearer),
    uow: UnitOfWorkConnection = Depends(get_uow),
    auth: AuthService = Depends(get_auth_service),
) -> AuthenticatedUser:
    """Retorna o usuário autenticado a partir do token JWT"""
    email = await auth.decode_access_token(token.credentials)
    if not email:
        raise UnauthorizedError
    repo = UserRepository(uow)  # Repository de usuários
    user = await repo.get_user_by_email(email)
    if not user:
        raise UnauthorizedError
    role = getattr(user, "role", RoleEnum.user)
    return AuthenticatedUser.model_validate({**user.to_dict(), "role": role})


def require_admin(
    user: AuthenticatedUser = Depends(get_current_user),
) -> AuthenticatedUser:
    if user.role != RoleEnum.admin:
        raise UnauthorizedError
    return user
