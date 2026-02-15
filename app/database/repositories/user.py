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

            if "password" in data and data["password"]:
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

    async def get_user_by_google_id(self, google_id: str) -> User | None:
        """Busca um usuário pelo Google ID."""
        session = await self.uow.get_session()
        query = (
            select(self.model)
            .filter(self.model.google_id == google_id)
            .filter(
                self.model.deleted_at.is_(None),
                self.model.deleted_by.is_(None),
            )
        )
        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def get_or_create_google_user(
        self, google_id: str, email: str, name: str
    ) -> User:
        """Busca ou cria um usuário a partir de dados do Google."""
        # Verifica se já existe usuário com esse google_id
        user = await self.get_user_by_google_id(google_id)
        if user:
            return user

        # Verifica se já existe usuário com esse email (migração de local para google)
        user = await self.get_user_by_email(email)
        if user:
            # Associa google_id ao usuário existente
            user.google_id = google_id
            user.provider = "google"
            session = await self.uow.get_session()
            await session.commit()
            await session.refresh(user)
            return user

        # Cria novo usuário
        username = await self._generate_unique_username(email)
        new_user = User(
            email=email,
            name=name,
            username=username,
            provider="google",
            google_id=google_id,
            password=None,  # Sem senha para usuários Google
            role="user",
            is_active=True,
            created_by="google_oauth",
        )

        session = await self.uow.get_session()
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        return new_user

    async def _generate_unique_username(self, email: str) -> str:
        """Gera um username único baseado no email."""
        base_username = email.split("@")[0]
        username = base_username
        counter = 1

        session = await self.uow.get_session()
        while True:
            query = select(self.model).filter(self.model.username == username)
            result = await session.execute(query)
            if not result.scalar_one_or_none():
                return username
            username = f"{base_username}{counter}"
            counter += 1
