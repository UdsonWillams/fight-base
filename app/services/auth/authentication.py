import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import bcrypt
from jose import JWTError, jwt

from app.core.settings import get_settings
from app.database.models.base import User
from app.database.repositories.user import UserRepository
from app.database.unit_of_work import UnitOfWorkConnection
from app.schemas.auth import RoleEnum, Token


class AuthService:
    def __init__(self):
        self.settings = get_settings()

    async def get_password_hash(self, password: str) -> str:
        # Bcrypt has a 72 byte limit, truncate if necessary
        password_bytes = password.encode("utf-8")[:72]
        salt = await asyncio.to_thread(bcrypt.gensalt)
        hashed = await asyncio.to_thread(bcrypt.hashpw, password_bytes, salt)
        return hashed.decode("utf-8")

    async def verify_password(self, plain: str, hashed: str) -> bool:
        # Bcrypt has a 72 byte limit, truncate if necessary
        plain_bytes = plain.encode("utf-8")[:72]
        hashed_bytes = hashed.encode("utf-8")
        result = await asyncio.to_thread(bcrypt.checkpw, plain_bytes, hashed_bytes)
        return result

    async def create_access_token(
        self, subject: str, extra: Optional[Dict[str, Any]] = None
    ) -> str:
        now_utc = datetime.now(timezone.utc)
        to_encode: dict = {"sub": subject, "iat": int(now_utc.timestamp())}
        if extra:
            to_encode.update(extra)
        expire_dt = now_utc + self.settings.ACCESS_TOKEN_EXPIRE_DELTA
        to_encode["exp"] = int(expire_dt.timestamp())
        return await asyncio.to_thread(
            jwt.encode, to_encode, self.settings.SECRET_KEY, self.settings.ALGORITHM
        )

    async def decode_access_token(self, token: str) -> Optional[str]:
        try:
            payload = await asyncio.to_thread(
                jwt.decode,
                token,
                self.settings.SECRET_KEY,
                [self.settings.ALGORITHM],
            )
            return payload.get("sub")
        except JWTError:
            return None

    async def authenticate(
        self, email: str, password: str, uow: UnitOfWorkConnection
    ) -> User | None:
        repository = UserRepository(uow)
        user = await repository.get_user_by_email(email)
        if not user:
            return None
        if not await self.verify_password(password, user.password):
            return None
        return user

    async def issue_token(self, email: str, uow: UnitOfWorkConnection) -> Token:
        repo = UserRepository(uow)
        user = await repo.get_user_by_email(email)
        role = getattr(user, "role", RoleEnum.user) if user else RoleEnum.user
        token_str = await self.create_access_token(subject=email, extra={"role": role})
        return Token(access_token=token_str)


def get_auth_service() -> AuthService:
    return AuthService()
