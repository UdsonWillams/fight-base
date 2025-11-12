import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.settings import get_settings
from app.database.models.base import User


async def create_admin():
    import bcrypt
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker

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
            print(f"[INFO] Admin já existe: {email} (ID: {existing.id})")
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
        )
        session.add(user)

        try:
            await session.commit()
            print(f"[OK] Admin criado: {user.email} (ID: {user.id})")
        except Exception as error:
            await session.rollback()
            print(f"[ERROR] Erro ao criar admin: {str(error)}")

    await engine.dispose()


def main():
    asyncio.run(create_admin())


if __name__ == "__main__":
    main()
