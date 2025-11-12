from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.logger import logger
from app.database.models.base import User
from app.database.repositories.base import BaseRepository
from app.database.unit_of_work import UnitOfWorkConnection
from app.exceptions.exceptions import RepositoryError


class UserRepository(BaseRepository[User]):
    """Repository para gerenciamento de usuários do sistema."""

    def __init__(self, uow: UnitOfWorkConnection):
        super().__init__(User, uow)

    async def get_user_by_email(self, email: str) -> User | None:
        """Busca um usuário por email."""
        session = await self.uow.get_session()
        query = (
            select(self.model)
            .filter(self.model.email == email)
            .filter(
                self.model.deleted_at.is_(None),
                self.model.deleted_by.is_(None),
            )
        )
        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def create(self, data: User) -> User:
        """Cria um novo usuário com senha criptografada."""
        try:
            session = await self.uow.get_session()
            from app.services.auth.authentication import AuthService

            crypt_service = AuthService()
            data.password = await crypt_service.get_password_hash(data.password)
            session.add(data)
            await session.commit()
            await session.refresh(data)
            return data
        except Exception as e:
            logger.error(f"Error creating {self.model.__name__}: {e}")
            raise RepositoryError

    async def update(self, id: Any, data: dict, updated_by="system") -> User | None:
        """Atualiza um usuário existente."""
        try:
            session = await self.uow.get_session()
            query = select(self.model).filter(self.model.id == id)
            result = await session.execute(query)
            existing_record = result.scalar_one_or_none()

            if not existing_record:
                return None

            for key, value in data.items():
                if key == "id" or not hasattr(existing_record, key):
                    continue
                setattr(existing_record, key, value)

            if "password" in data:
                from app.services.auth.authentication import AuthService

                crypt_service = AuthService()
                existing_record.password = await crypt_service.get_password_hash(
                    data["password"]
                )

            existing_record.updated_at = datetime.now(timezone.utc)
            existing_record.updated_by = updated_by

            await session.commit()
            await session.refresh(existing_record)
            return existing_record
        except IntegrityError as ie:
            logger.error(f"Integrity error updating {self.model.__name__}: {ie}")
            raise RepositoryError("Integrity error")
        except Exception as e:
            logger.error(f"Error updating {self.model.__name__}: {e}")
            raise RepositoryError
