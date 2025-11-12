import sys
import uuid

import pytest_asyncio
from passlib.context import CryptContext

from app.database.models.base import User
from app.schemas.external.fake_products.products import Products

sys.path.append("app/")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
RAW_TEST_PASSWORD = "testpassword"
HASHED_TEST_PASSWORD = pwd_context.hash(RAW_TEST_PASSWORD)


@pytest_asyncio.fixture(scope="function")
async def user(async_session):
    base_entity = User(
        id=uuid.uuid4(),
        email=f"test{uuid.uuid4()}mail@mail.com",
        name="Test User",
        password=HASHED_TEST_PASSWORD,
        is_active=True,
        role="user",
    )
    async_session.add(base_entity)
    await async_session.commit()
    await async_session.refresh(base_entity)
    base_entity.plain_password = RAW_TEST_PASSWORD
    return base_entity


@pytest_asyncio.fixture(scope="function")
async def user_admin(async_session):
    base_entity = User(
        id=uuid.uuid4(),
        email=f"test{uuid.uuid4()}mail@mail.com",
        name="Test User",
        password=HASHED_TEST_PASSWORD,
        is_active=True,
        role="admin",
    )
    async_session.add(base_entity)
    await async_session.commit()
    await async_session.refresh(base_entity)
    base_entity.plain_password = RAW_TEST_PASSWORD
    return base_entity


@pytest_asyncio.fixture(scope="function")
async def some_users(async_session):
    """Fixture to create multiple User instances."""
    users_list = []
    for _ in range(5):
        c = User(
            id=uuid.uuid4(),
            email=f"testmail{uuid.uuid4()}@mail.com",
            name="Test User",
            password=HASHED_TEST_PASSWORD,
            is_active=True,
            role="user",
        )
        async_session.add(c)
        await async_session.commit()
        await async_session.refresh(c)
        c.plain_password = RAW_TEST_PASSWORD
        users_list.append(c)
    return users_list


@pytest_asyncio.fixture(scope="function")
async def products(async_session, user):
    base_entity = Products(
        id=uuid.uuid4(),
        title="Test Product",
        description="This is a test product",
        price=10.99,
        category="Test Category",
        image="http://example.com/image.jpg",
        review=4.5,
        external_id="external-123",
        user_id=user.id,
    )
    async_session.add(base_entity)
    await async_session.commit()
    await async_session.refresh(base_entity)
    return base_entity
