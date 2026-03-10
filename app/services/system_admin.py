"""
Service para criar usuário administrador do sistema
"""

import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.settings import get_settings
from app.database.models.base import User
from app.core.logger import logger


async def create_admin():
    """
    Cria o usuário administrador padrão do sistema se não existir.
    Utiliza as configurações de ADMIN_DEFAULT_EMAIL, ADMIN_DEFAULT_PASSWORD e ADMIN_DEFAULT_ROLE.
    """
    s = get_settings()
    email, password, role = (
        s.ADMIN_DEFAULT_EMAIL,
        s.ADMIN_DEFAULT_PASSWORD,
        s.ADMIN_DEFAULT_ROLE,
    )

    # Criar engine diretamente
    engine = create_async_engine(s.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Verificar se admin já existe
        result = await session.execute(select(User).where(User.email == email))
        existing = result.scalar_one_or_none()

        if existing:
            logger.info(f"[INFO] Admin já existe: {email} (ID: {existing.id})")
            return

        # Criar hash da senha usando bcrypt diretamente
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode(
            "utf-8"
        )

        # Criar usuário admin
        user = User(
            email=email,
            password=hashed,
            name="Administrator",
            role=role,
            is_active=True,
            username="elemesmo",
            created_by="system",
            updated_by="system",
        )
        session.add(user)

        try:
            await session.commit()
            logger.info(f"[OK] Admin criado: {user.email} (ID: {user.id})")
        except Exception as error:
            await session.rollback()
            logger.info(f"[ERROR] Erro ao criar admin: {str(error)}")

    await engine.dispose()
