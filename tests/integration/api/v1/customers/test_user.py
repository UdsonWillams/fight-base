import pytest
from fastapi import status
from httpx import AsyncClient

from app.database.models.base import User


async def _get_token_for_customer(client, customer):
    resp = await client.post(
        "api/v1/auth/token",
        json={"email": customer.email, "password": customer.plain_password},
    )
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    return headers


@pytest.mark.asyncio
async def test_create(client: AsyncClient):
    payload = {
        "email": "user_integration@example.com",
        "password": "pass123",
        "name": "User Integration",
        "username": "integration_test_user",
    }
    resp = await client.post("api/v1/users", json=payload)
    assert resp.status_code == status.HTTP_201_CREATED
    data = resp.json()
    assert data["email"] == payload["email"]
    assert "id" in data


@pytest.mark.asyncio
async def test_get_customer(client: AsyncClient, user: User):
    headers = await _get_token_for_customer(client, user)
    resp = await client.get(f"api/v1/users/{user.id}", headers=headers)
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["id"] == str(user.id)
    assert data["email"] == user.email


@pytest.mark.asyncio
async def test_list_customers(
    client: AsyncClient, user_admin: User, some_users: list[User]
):
    headers = await _get_token_for_customer(client, user_admin)
    resp = await client.get("api/v1/users", headers=headers)
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert "items" in data


@pytest.mark.asyncio
async def test_update_customer(client: AsyncClient, user: User):
    headers = await _get_token_for_customer(client, user)
    payload = {"name": "Updated Name"}
    resp = await client.put(
        f"api/v1/users/{user.id}", json=payload, headers=headers
    )
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["name"] == payload["name"]


@pytest.mark.asyncio
async def test_delete_customer(
    client: AsyncClient, user: User, user_admin: User
):
    headers = await _get_token_for_customer(client, user_admin)
    resp = await client.delete(f"api/v1/users/{user.id}", headers=headers)
    assert resp.status_code == status.HTTP_204_NO_CONTENT

    # Verify deletion
    get_resp = await client.get(f"api/v1/users/{user.id}", headers=headers)
    assert get_resp.status_code == status.HTTP_404_NOT_FOUND
