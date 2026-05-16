import uuid

import pytest
from fastapi import status
from httpx import AsyncClient

from app.database.models.base import User, Fighter


async def _get_token(client, user):
    resp = await client.post(
        "api/v1/auth/token",
        json={"email": user.email, "password": user.plain_password},
    )
    assert resp.status_code == status.HTTP_200_OK
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


class TestCreateEvent:
    @pytest.mark.asyncio
    async def test_create_event_success(
        self, client: AsyncClient, user: User, fighter: Fighter, fighter2: Fighter
    ):
        headers = await _get_token(client, user)
        payload = {
            "name": "UFC 300",
            "date": "2025-06-15T00:00:00Z",
            "organization": "UFC",
            "fights": [
                {
                    "fighter1_id": str(fighter.id),
                    "fighter2_id": str(fighter2.id),
                    "fight_order": 1,
                }
            ],
        }
        resp = await client.post("api/v1/events/", json=payload, headers=headers)

        assert resp.status_code == status.HTTP_201_CREATED
        data = resp.json()
        assert data["name"] == "UFC 300"
        assert data["organization"] == "UFC"
        assert data["status"] == "scheduled"

    @pytest.mark.asyncio
    async def test_create_event_without_auth_returns_401(self, client: AsyncClient):
        payload = {"name": "UFC 300", "organization": "UFC"}
        resp = await client.post("api/v1/events/", json=payload)
        assert resp.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    @pytest.mark.asyncio
    async def test_create_event_missing_name_returns_422(
        self, client: AsyncClient, user: User
    ):
        headers = await _get_token(client, user)
        payload = {"organization": "UFC"}
        resp = await client.post("api/v1/events/", json=payload, headers=headers)
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestListEvents:
    @pytest.mark.asyncio
    async def test_list_events_empty(self, client: AsyncClient, user: User):
        headers = await _get_token(client, user)
        resp = await client.get("api/v1/events/", headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_list_events_with_created(
        self, client: AsyncClient, user: User, fighter: Fighter, fighter2: Fighter
    ):
        headers = await _get_token(client, user)
        fight_data = [
            {
                "fighter1_id": str(fighter.id),
                "fighter2_id": str(fighter2.id),
                "fight_order": 1,
            }
        ]
        await client.post(
            "api/v1/events/",
            json={
                "name": "UFC 300",
                "date": "2025-06-15T00:00:00Z",
                "organization": "UFC",
                "fights": fight_data,
            },
            headers=headers,
        )
        await client.post(
            "api/v1/events/",
            json={
                "name": "Bellator 250",
                "date": "2025-07-01T00:00:00Z",
                "organization": "Bellator",
                "fights": fight_data,
            },
            headers=headers,
        )

        resp = await client.get("api/v1/events/", headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert len(data) == 2

    @pytest.mark.asyncio
    async def test_list_events_filter_by_organization(
        self, client: AsyncClient, user: User, fighter: Fighter, fighter2: Fighter
    ):
        headers = await _get_token(client, user)
        fight_data = [
            {
                "fighter1_id": str(fighter.id),
                "fighter2_id": str(fighter2.id),
                "fight_order": 1,
            }
        ]
        await client.post(
            "api/v1/events/",
            json={
                "name": "UFC 300",
                "date": "2025-06-15T00:00:00Z",
                "organization": "UFC",
                "fights": fight_data,
            },
            headers=headers,
        )
        await client.post(
            "api/v1/events/",
            json={
                "name": "ONE 100",
                "date": "2025-08-01T00:00:00Z",
                "organization": "ONE",
                "fights": fight_data,
            },
            headers=headers,
        )

        resp = await client.get("api/v1/events/?organization=UFC", headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert len(data) == 1
        assert data[0]["organization"] == "UFC"

    @pytest.mark.asyncio
    async def test_list_events_without_auth_returns_401(
        self, client: AsyncClient
    ):
        resp = await client.get("api/v1/events/")
        assert resp.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )


class TestGetEvent:
    @pytest.mark.asyncio
    async def test_get_event_not_found(self, client: AsyncClient, user: User):
        headers = await _get_token(client, user)
        resp = await client.get(f"api/v1/events/{uuid.uuid4()}", headers=headers)
        assert resp.status_code == status.HTTP_404_NOT_FOUND


class TestDeleteEvent:
    @pytest.mark.asyncio
    async def test_delete_event_requires_auth(self, client: AsyncClient):
        resp = await client.delete(f"api/v1/events/{uuid.uuid4()}")
        assert resp.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )
