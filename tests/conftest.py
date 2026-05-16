import os

os.environ["APP_ENVIRONMENT"] = "local"

import sys

from httpx import ASGITransport, AsyncClient

from app.database.unit_of_work import get_uow

sys.path.append("app/")

import pytest
import pytest_asyncio

# This will automatically include the fixtures from the specified modules
# Need to update this list as you add more fixture files
pytest_plugins = [
    "tests.fixtures.database_sqlite",
    "tests.fixtures.base",
]


@pytest.fixture(scope="function")
def app(uow):
    from app.main import app

    app.dependency_overrides[get_uow] = lambda: uow
    yield app


@pytest_asyncio.fixture(scope="function")
async def client(async_session, uow):
    from starlette.routing import _DefaultLifespan

    from app.main import app

    app.dependency_overrides[get_uow] = lambda: uow
    app.router.lifespan_context = _DefaultLifespan(app.router)
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://localhost"
    ) as ac:
        yield ac


@pytest_asyncio.fixture(scope="function")
async def admin_headers(client, user_admin):
    resp = await client.post(
        "/auth/token",
        json={"email": user_admin.email, "password": user_admin.plain_password},
    )
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def customer_admin(user_admin):
    return user_admin


@pytest.fixture
def customer(user):
    return user


@pytest.fixture
def some_customers(some_users):
    return some_users
