import pytest
from fastapi import status
from httpx import AsyncClient

from app.database.models.base import User


async def _get_token(client, user):
    resp = await client.post(
        "api/v1/auth/token",
        json={"email": user.email, "password": user.plain_password},
    )
    assert resp.status_code == status.HTTP_200_OK
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


class TestCreateLeague:
    @pytest.mark.asyncio
    async def test_create_league_success(self, client: AsyncClient, user: User):
        headers = await _get_token(client, user)
        payload = {
            "name": "Minha Liga",
            "description": "Liga de teste",
            "max_members": 20,
        }
        resp = await client.post("api/v1/leagues/", json=payload, headers=headers)

        assert resp.status_code == status.HTTP_201_CREATED
        data = resp.json()
        assert data["name"] == "Minha Liga"
        assert data["description"] == "Liga de teste"
        assert "invite_code" in data
        assert len(data["invite_code"]) == 8
        assert data["owner_id"] == str(user.id)
        assert data["members_count"] == 1

    @pytest.mark.asyncio
    async def test_create_league_minimal_payload(self, client: AsyncClient, user: User):
        headers = await _get_token(client, user)
        payload = {"name": "Liga Simples"}
        resp = await client.post("api/v1/leagues/", json=payload, headers=headers)

        assert resp.status_code == status.HTTP_201_CREATED
        data = resp.json()
        assert data["name"] == "Liga Simples"
        assert data["members_count"] == 1

    @pytest.mark.asyncio
    async def test_create_league_without_auth_returns_401(
        self, client: AsyncClient
    ):
        payload = {"name": "Liga Sem Auth"}
        resp = await client.post("api/v1/leagues/", json=payload)
        assert resp.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)

    @pytest.mark.asyncio
    async def test_create_league_empty_name_returns_422(
        self, client: AsyncClient, user: User
    ):
        headers = await _get_token(client, user)
        payload = {"name": ""}
        resp = await client.post("api/v1/leagues/", json=payload, headers=headers)
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_create_league_missing_name_returns_422(
        self, client: AsyncClient, user: User
    ):
        headers = await _get_token(client, user)
        payload = {"max_members": 10}
        resp = await client.post("api/v1/leagues/", json=payload, headers=headers)
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_create_league_generates_unique_invite_codes(
        self, client: AsyncClient, user: User
    ):
        headers = await _get_token(client, user)
        codes = set()
        for i in range(3):
            payload = {"name": f"Liga {i}"}
            resp = await client.post("api/v1/leagues/", json=payload, headers=headers)
            assert resp.status_code == status.HTTP_201_CREATED
            codes.add(resp.json()["invite_code"])
        assert len(codes) == 3


class TestJoinLeague:
    async def _create_league(self, client, user, name="Liga Join", max_members=10):
        headers = await _get_token(client, user)
        resp = await client.post(
            "api/v1/leagues/",
            json={"name": name, "max_members": max_members},
            headers=headers,
        )
        assert resp.status_code == status.HTTP_201_CREATED
        return resp.json()

    @pytest.mark.asyncio
    async def test_join_league_success(
        self, client: AsyncClient, user: User, user_admin: User
    ):
        league = await self._create_league(client, user, max_members=10)
        invite_code = league["invite_code"]

        headers = await _get_token(client, user_admin)
        resp = await client.post(
            f"api/v1/leagues/join/{invite_code}", headers=headers
        )

        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["id"] == league["id"]
        assert data["name"] == league["name"]

    @pytest.mark.asyncio
    async def test_join_league_invalid_code_returns_400(
        self, client: AsyncClient, user: User
    ):
        headers = await _get_token(client, user)
        resp = await client.post(
            "api/v1/leagues/join/INVALID1", headers=headers
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        data = resp.json()
        assert "message" in data

    @pytest.mark.asyncio
    async def test_join_league_already_member_returns_400(
        self, client: AsyncClient, user: User
    ):
        league = await self._create_league(client, user)
        invite_code = league["invite_code"]

        headers = await _get_token(client, user)
        resp = await client.post(
            f"api/v1/leagues/join/{invite_code}", headers=headers
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert "já faz parte" in resp.json()["message"]

    @pytest.mark.asyncio
    async def test_join_league_full_returns_400(
        self, client: AsyncClient, user: User, user_admin: User, some_users: list[User]
    ):
        league = await self._create_league(client, user_admin, max_members=2)

        user_headers = await _get_token(client, user)
        resp = await client.post(
            f"api/v1/leagues/join/{league['invite_code']}", headers=user_headers
        )
        assert resp.status_code == status.HTTP_200_OK

        third_user = some_users[0]
        third_headers = await _get_token(client, third_user)
        resp = await client.post(
            f"api/v1/leagues/join/{league['invite_code']}", headers=third_headers
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert "limite máximo" in resp.json()["message"]

    @pytest.mark.asyncio
    async def test_join_league_without_auth_returns_401(
        self, client: AsyncClient, user: User
    ):
        league = await self._create_league(client, user)
        resp = await client.post(f"api/v1/leagues/join/{league['invite_code']}")
        assert resp.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)


class TestGetMyLeagues:
    async def _create_league(self, client, user, name="Liga List", max_members=10):
        headers = await _get_token(client, user)
        resp = await client.post(
            "api/v1/leagues/",
            json={"name": name, "max_members": max_members},
            headers=headers,
        )
        assert resp.status_code == status.HTTP_201_CREATED
        return resp.json()

    @pytest.mark.asyncio
    async def test_list_user_leagues(self, client: AsyncClient, user: User):
        await self._create_league(client, user, name="Liga A")
        await self._create_league(client, user, name="Liga B")

        headers = await _get_token(client, user)
        resp = await client.get("api/v1/leagues/my", headers=headers)

        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 2
        names = {item["name"] for item in data}
        assert names == {"Liga A", "Liga B"}

    @pytest.mark.asyncio
    async def test_list_empty_when_no_leagues(
        self, client: AsyncClient, user: User
    ):
        headers = await _get_token(client, user)
        resp = await client.get("api/v1/leagues/my", headers=headers)

        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 0

    @pytest.mark.asyncio
    async def test_list_only_shows_user_leagues(
        self, client: AsyncClient, user: User, user_admin: User
    ):
        await self._create_league(client, user, name="Liga do User")
        await self._create_league(client, user_admin, name="Liga do Admin")

        headers = await _get_token(client, user)
        resp = await client.get("api/v1/leagues/my", headers=headers)

        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        names = {item["name"] for item in data}
        assert "Liga do User" in names
        assert "Liga do Admin" not in names

    @pytest.mark.asyncio
    async def test_list_without_auth_returns_401(self, client: AsyncClient):
        resp = await client.get("api/v1/leagues/my")
        assert resp.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)
