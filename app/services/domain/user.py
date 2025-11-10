from app.database.models.base import User
from app.database.repositories.user import UserRepository
from app.database.unit_of_work import UnitOfWorkConnection
from app.exceptions.exceptions import NotFoundError, UnauthorizedError
from app.schemas.auth import AuthenticatedUser
from app.schemas.domain.users import output
from app.schemas.domain.users.input import CreateUser


class UserService:
    """Service para gerenciamento de usuários do sistema."""

    def __init__(self, uow: UnitOfWorkConnection, user: AuthenticatedUser = None):
        self.uow = uow
        self.user = user
        self.repository = UserRepository(uow)

    async def create_user(self, payload: CreateUser):
        """Cria um novo usuário."""
        user = await self.repository.create(User(**payload.model_dump()))
        return user.to_dict()

    async def list_all(
        self,
        sort_by: str = "-updated_at",
        filters: dict = {},
        page_size: int = 100,
        page: int = 0,
    ):
        """Lista todos os usuários com paginação."""
        users = await self.repository.get(filters, sort_by, page_size, page)
        data = []
        for user in users:
            data.append(output.UserResponse(**user.to_dict()))

        return {"items": data, "count": len(data) if data else 0}

    async def get_by_id(self, user_id: int):
        """Busca usuário por ID com seus lutadores."""
        user = await self.repository.get_by_id(user_id)
        if not user:
            raise NotFoundError
        result = user.to_dict()
        # Carregar lutadores do usuário se necessário
        result["fighters"] = [
            fighter.to_dict() for fighter in getattr(user, "fighters", [])
        ]
        return result

    async def get_by_email(self, email: str):
        """Busca usuário por email."""
        user = await self.repository.get_user_by_email(email)
        if not user:
            raise NotFoundError
        result = user.to_dict()
        result["fighters"] = [
            fighter.to_dict() for fighter in getattr(user, "fighters", [])
        ]
        return result

    async def update(self, user_id: int, payload: dict):
        """Atualiza dados do usuário."""
        if (
            self.user
            and str(self.user.id) != str(user_id)
            and self.user.role != "admin"
        ):
            raise UnauthorizedError
        updated_user = await self.repository.update(
            user_id, payload, self.user.email if self.user else "system"
        )
        if not updated_user:
            raise NotFoundError
        return updated_user.to_dict()

    async def delete(self, user_id: int):
        """Deleta um usuário (soft delete)."""
        if (
            self.user
            and str(self.user.id) != str(user_id)
            and self.user.role != "admin"
        ):
            raise UnauthorizedError
        if not await self.repository.delete(user_id):
            raise NotFoundError
