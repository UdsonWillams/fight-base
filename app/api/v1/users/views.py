from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.v1.auth.dependencies import get_current_user, require_admin
from app.database.unit_of_work import UnitOfWorkConnection, get_uow
from app.schemas.auth import AuthenticatedUser
from app.schemas.domain.users import input, output
from app.services.domain.user import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.post(
    "",
    response_model=output.CreateUserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_user(
    payload: input.CreateUser, uow: UnitOfWorkConnection = Depends(get_uow)
):
    """Cria um novo usuário no sistema."""
    service = UserService(uow)
    response = await service.create_user(payload)
    return response


@router.get("", response_model=output.UserList, status_code=status.HTTP_200_OK)
async def list_users(
    page_size: int = 100,
    page: int = 1,
    sort_by: str | None = "-updated_at",
    admin: AuthenticatedUser = Depends(require_admin),
    uow: UnitOfWorkConnection = Depends(get_uow),
):
    """Lista todos os usuários (apenas admin)."""
    service = UserService(uow)
    response = await service.list_all(
        sort_by=sort_by, filters={}, page=page, page_size=page_size
    )
    return response


@router.get(
    "/{user_id}",
    response_model=output.UserResponse,
    status_code=status.HTTP_200_OK,
)
async def get_user(
    user_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    uow: UnitOfWorkConnection = Depends(get_uow),
):
    """Busca um usuário por ID."""
    service = UserService(uow, current_user)
    user = await service.get_by_id(user_id)
    return user


@router.get(
    "/email/{email}",
    response_model=output.UserResponse,
    status_code=status.HTTP_200_OK,
)
async def get_user_by_email(
    email: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    uow: UnitOfWorkConnection = Depends(get_uow),
):
    """Busca um usuário por email."""
    service = UserService(uow, current_user)
    user = await service.get_by_email(email)
    return user


@router.put(
    "/{user_id}",
    response_model=output.UserResponse,
    status_code=status.HTTP_200_OK,
)
async def update_user(
    user_id: UUID,
    payload: input.UpdateUser,
    current_user: AuthenticatedUser = Depends(get_current_user),
    uow: UnitOfWorkConnection = Depends(get_uow),
):
    """Atualiza dados de um usuário."""
    service = UserService(uow, current_user)
    updated = await service.update(user_id, payload.model_dump(exclude_unset=True))
    return updated


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    admin: AuthenticatedUser = Depends(require_admin),
    uow: UnitOfWorkConnection = Depends(get_uow),
):
    """Deleta um usuário (soft delete, apenas admin)."""
    service = UserService(uow, admin)
    await service.delete(user_id)
    return None
