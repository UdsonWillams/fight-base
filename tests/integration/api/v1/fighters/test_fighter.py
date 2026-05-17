"""
Testes de integracao para API de Fighters (CRUD, search, rankings, stats).
Usa SQLite em memoria para validacao real de persistencia.
"""

import pytest
from fastapi import status
from httpx import AsyncClient

from app.database.models.base import Fighter, User


async def _get_token(client, user):
    resp = await client.post(
        "api/v1/auth/token",
        json={"email": user.email, "password": user.plain_password},
    )
    assert resp.status_code == status.HTTP_200_OK
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


FIGHTER_PAYLOAD = {
    "name": "Jon Jones",
    "nickname": "Bones",
    "last_organization_fight": "UFC",
    "actual_weight_class": "Heavyweight",
    "fighting_style": "All-around",
    "striking": 85,
    "grappling": 90,
    "defense": 80,
    "stamina": 75,
    "speed": 70,
    "strategy": 88,
}


class TestCreateFighter:
    """POST /api/v1/fighters/"""

    @pytest.mark.asyncio
    async def test_create_fighter_success(self, client: AsyncClient, user: User):
        headers = await _get_token(client, user)
        resp = await client.post(
            "api/v1/fighters/", json=FIGHTER_PAYLOAD, headers=headers
        )
        assert resp.status_code == status.HTTP_201_CREATED
        data = resp.json()
        assert data["name"] == "Jon Jones"
        assert data["nickname"] == "Bones"
        assert data["actual_weight_class"] == "Heavyweight"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_fighter_without_auth_returns_401(
        self, client: AsyncClient
    ):
        resp = await client.post("api/v1/fighters/", json=FIGHTER_PAYLOAD)
        assert resp.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    @pytest.mark.asyncio
    async def test_create_fighter_missing_name_returns_422(
        self, client: AsyncClient, user: User
    ):
        headers = await _get_token(client, user)
        payload = {k: v for k, v in FIGHTER_PAYLOAD.items() if k != "name"}
        resp = await client.post(
            "api/v1/fighters/", json=payload, headers=headers
        )
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_create_fighter_short_name_returns_422(
        self, client: AsyncClient, user: User
    ):
        headers = await _get_token(client, user)
        payload = {**FIGHTER_PAYLOAD, "name": "X"}
        resp = await client.post(
            "api/v1/fighters/", json=payload, headers=headers
        )
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_create_fighter_invalid_striking_returns_422(
        self, client: AsyncClient, user: User
    ):
        headers = await _get_token(client, user)
        payload = {**FIGHTER_PAYLOAD, "striking": 101}
        resp = await client.post(
            "api/v1/fighters/", json=payload, headers=headers
        )
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestGetFighter:
    """GET /api/v1/fighters/{fighter_id}"""

    @pytest.mark.asyncio
    async def test_get_fighter_by_id(self, client: AsyncClient, fighter: Fighter):
        resp = await client.get(f"api/v1/fighters/{fighter.id}")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["id"] == str(fighter.id)
        assert data["name"] == fighter.name

    @pytest.mark.asyncio
    async def test_get_fighter_not_found_returns_404(self, client: AsyncClient):
        resp = await client.get(
            "api/v1/fighters/00000000-0000-0000-0000-000000000000"
        )
        assert resp.status_code == status.HTTP_404_NOT_FOUND


class TestUpdateFighter:
    """PUT /api/v1/fighters/{fighter_id}"""

    @pytest.mark.asyncio
    async def test_update_fighter_success(
        self, client: AsyncClient, user: User, fighter: Fighter
    ):
        headers = await _get_token(client, user)
        payload = {"name": "Updated Name", "striking": 99}
        resp = await client.put(
            f"api/v1/fighters/{fighter.id}", json=payload, headers=headers
        )
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["name"] == "Updated Name"

    @pytest.mark.asyncio
    async def test_update_fighter_without_auth_returns_401(
        self, client: AsyncClient, fighter: Fighter
    ):
        resp = await client.put(
            f"api/v1/fighters/{fighter.id}", json={"name": "X"}
        )
        assert resp.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    @pytest.mark.asyncio
    async def test_update_fighter_not_found_returns_404(
        self, client: AsyncClient, user: User
    ):
        headers = await _get_token(client, user)
        resp = await client.put(
            "api/v1/fighters/00000000-0000-0000-0000-000000000000",
            json={"name": "Ghost"},
            headers=headers,
        )
        assert resp.status_code == status.HTTP_404_NOT_FOUND


class TestDeleteFighter:
    """DELETE /api/v1/fighters/{fighter_id}"""

    @pytest.mark.asyncio
    async def test_delete_fighter_success(
        self, client: AsyncClient, user: User, fighter: Fighter
    ):
        headers = await _get_token(client, user)
        resp = await client.delete(
            f"api/v1/fighters/{fighter.id}", headers=headers
        )
        assert resp.status_code == status.HTTP_204_NO_CONTENT

        get_resp = await client.get(f"api/v1/fighters/{fighter.id}")
        assert get_resp.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_delete_fighter_without_auth_returns_401(
        self, client: AsyncClient, fighter: Fighter
    ):
        resp = await client.delete(f"api/v1/fighters/{fighter.id}")
        assert resp.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )


class TestSearchFighters:
    """GET /api/v1/fighters/"""

    @pytest.mark.asyncio
    async def test_search_returns_fighters(
        self, client: AsyncClient, fighter: Fighter
    ):
        resp = await client.get("api/v1/fighters/")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert "fighters" in data
        assert "total" in data
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_search_by_name(self, client: AsyncClient, fighter: Fighter):
        resp = await client.get(
            f"api/v1/fighters/?name={fighter.name}"
        )
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert any(f["name"] == fighter.name for f in data["fighters"])

    @pytest.mark.asyncio
    async def test_search_by_name_no_match(self, client: AsyncClient):
        resp = await client.get("api/v1/fighters/?name=ZzzNotExists123")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_search_pagination(self, client: AsyncClient, fighter: Fighter):
        resp = await client.get("api/v1/fighters/?limit=1&offset=0")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["limit"] == 1
        assert len(data["fighters"]) <= 1


class TestRankingsTop:
    """GET /api/v1/fighters/rankings/top"""

    @pytest.mark.asyncio
    async def test_rankings_returns_list(self, client: AsyncClient, fighter: Fighter):
        resp = await client.get("api/v1/fighters/rankings/top")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_rankings_with_limit(self, client: AsyncClient, fighter: Fighter):
        resp = await client.get("api/v1/fighters/rankings/top?limit=5")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert len(data) <= 5


class TestFighterStatistics:
    """GET /api/v1/fighters/statistics/overview"""

    @pytest.mark.asyncio
    async def test_statistics_returns_data(self, client: AsyncClient, fighter: Fighter):
        resp = await client.get("api/v1/fighters/statistics/overview")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert "total_fighters" in data
        assert data["total_fighters"] >= 1
        assert "total_real" in data
        assert "total_fictional" in data


class TestMyFighters:
    """GET /api/v1/fighters/my/fighters"""

    @pytest.mark.asyncio
    async def test_my_fighters_requires_auth(self, client: AsyncClient):
        resp = await client.get("api/v1/fighters/my/fighters")
        assert resp.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    @pytest.mark.asyncio
    async def test_my_fighters_returns_list(
        self, client: AsyncClient, user: User, fighter: Fighter
    ):
        headers = await _get_token(client, user)
        resp = await client.get(
            "api/v1/fighters/my/fighters", headers=headers
        )
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert isinstance(data, list)
        assert any(f["id"] == str(fighter.id) for f in data)
