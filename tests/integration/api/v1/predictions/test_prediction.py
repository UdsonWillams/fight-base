"""
Testes de integracao para API de Predictions (palpites, leaderboard, stats, achievements).
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


async def _create_event_with_fight(
    client, user, fighter1: Fighter, fighter2: Fighter
):
    headers = await _get_token(client, user)
    resp = await client.post(
        "api/v1/events/",
        json={
            "name": "Test Event Predictions",
            "date": "2025-06-15T00:00:00Z",
            "organization": "UFC",
            "fights": [
                {
                    "fighter1_id": str(fighter1.id),
                    "fighter2_id": str(fighter2.id),
                    "fight_order": 1,
                }
            ],
        },
        headers=headers,
    )
    assert resp.status_code == status.HTTP_201_CREATED
    return resp.json()


class TestCreatePrediction:
    """POST /api/v1/predictions/"""

    @pytest.mark.asyncio
    async def test_create_prediction_success(
        self,
        client: AsyncClient,
        user: User,
        fighter: Fighter,
        fighter2: Fighter,
    ):
        event = await _create_event_with_fight(client, user, fighter, fighter2)
        fight = event["fights"][0]

        headers = await _get_token(client, user)
        payload = {
            "fight_id": fight["id"],
            "event_id": event["id"],
            "predicted_winner_id": str(fighter.id),
        }
        resp = await client.post(
            "api/v1/predictions/", json=payload, headers=headers
        )

        assert resp.status_code == status.HTTP_201_CREATED
        data = resp.json()
        assert data["fight_id"] == fight["id"]
        assert data["event_id"] == event["id"]
        assert data["predicted_winner_id"] == str(fighter.id)
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_prediction_without_auth_returns_401(
        self, client: AsyncClient
    ):
        resp = await client.post("api/v1/predictions/", json={})
        assert resp.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    @pytest.mark.asyncio
    async def test_create_duplicate_prediction_returns_400(
        self,
        client: AsyncClient,
        user: User,
        fighter: Fighter,
        fighter2: Fighter,
    ):
        event = await _create_event_with_fight(client, user, fighter, fighter2)
        fight = event["fights"][0]

        headers = await _get_token(client, user)
        payload = {
            "fight_id": fight["id"],
            "event_id": event["id"],
            "predicted_winner_id": str(fighter.id),
        }

        resp1 = await client.post(
            "api/v1/predictions/", json=payload, headers=headers
        )
        assert resp1.status_code == status.HTTP_201_CREATED

        resp2 = await client.post(
            "api/v1/predictions/", json=payload, headers=headers
        )
        assert resp2.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.asyncio
    async def test_create_prediction_missing_fight_id_returns_422(
        self, client: AsyncClient, user: User
    ):
        headers = await _get_token(client, user)
        payload = {"event_id": "00000000-0000-0000-0000-000000000000"}
        resp = await client.post(
            "api/v1/predictions/", json=payload, headers=headers
        )
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestGetMyPredictionsForEvent:
    """GET /api/v1/predictions/my/event/{event_id}"""

    @pytest.mark.asyncio
    async def test_no_predictions_returns_empty(
        self, client: AsyncClient, user: User
    ):
        headers = await _get_token(client, user)
        resp = await client.get(
            "api/v1/predictions/my/event/00000000-0000-0000-0000-000000000000",
            headers=headers,
        )
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 0

    @pytest.mark.asyncio
    async def test_returns_predictions_after_creation(
        self,
        client: AsyncClient,
        user: User,
        fighter: Fighter,
        fighter2: Fighter,
    ):
        event = await _create_event_with_fight(client, user, fighter, fighter2)
        fight = event["fights"][0]

        headers = await _get_token(client, user)
        await client.post(
            "api/v1/predictions/",
            json={
                "fight_id": fight["id"],
                "event_id": event["id"],
                "predicted_winner_id": str(fighter.id),
            },
            headers=headers,
        )

        resp = await client.get(
            f"api/v1/predictions/my/event/{event['id']}", headers=headers
        )
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert len(data) == 1
        assert data[0]["fight_id"] == fight["id"]

    @pytest.mark.asyncio
    async def test_requires_auth(self, client: AsyncClient):
        resp = await client.get(
            "api/v1/predictions/my/event/00000000-0000-0000-0000-000000000000"
        )
        assert resp.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )


class TestEventLeaderboard:
    """GET /api/v1/predictions/leaderboard/event/{event_id}"""

    @pytest.mark.asyncio
    async def test_leaderboard_returns_list(
        self, client: AsyncClient
    ):
        resp = await client.get(
            "api/v1/predictions/leaderboard/event/00000000-0000-0000-0000-000000000000"
        )
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert isinstance(data, list)


class TestGetMyStats:
    """GET /api/v1/predictions/my/stats"""

    @pytest.mark.asyncio
    async def test_returns_default_stats_for_new_user(
        self, client: AsyncClient, user: User
    ):
        headers = await _get_token(client, user)
        resp = await client.get(
            "api/v1/predictions/my/stats", headers=headers
        )
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["total_points"] == 0
        assert data["total_predictions"] == 0
        assert data["correct_winners"] == 0
        assert "current_streak" in data
        assert "best_streak" in data

    @pytest.mark.asyncio
    async def test_requires_auth(self, client: AsyncClient):
        resp = await client.get("api/v1/predictions/my/stats")
        assert resp.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )


class TestFinishMethods:
    """GET /api/v1/predictions/finish-methods"""

    @pytest.mark.asyncio
    async def test_finish_methods_returns_list(self, client: AsyncClient):
        resp = await client.get("api/v1/predictions/finish-methods")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert isinstance(data, list)


class TestMyAchievements:
    """GET /api/v1/predictions/my/achievements"""

    @pytest.mark.asyncio
    async def test_returns_empty_for_new_user(
        self, client: AsyncClient, user: User
    ):
        headers = await _get_token(client, user)
        resp = await client.get(
            "api/v1/predictions/my/achievements", headers=headers
        )
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 0

    @pytest.mark.asyncio
    async def test_requires_auth(self, client: AsyncClient):
        resp = await client.get("api/v1/predictions/my/achievements")
        assert resp.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )
