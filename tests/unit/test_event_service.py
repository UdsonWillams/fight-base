from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.database.models.base import Event, Fight
from app.exceptions.exceptions import NotFoundError, ForbiddenError
from app.schemas.domain.events.input import CreateEvent, AddFightToEvent, CreateFight
from app.services.domain.event import EventService


def make_event(**kwargs):
    defaults = {
        "id": uuid4(),
        "name": "UFC 300",
        "date": None,
        "organization": "UFC",
        "status": "scheduled",
        "creator_id": uuid4(),
    }
    defaults.update(kwargs)
    return Event(**defaults)


def make_fight_create(**kwargs):
    defaults = {
        "fighter1_id": uuid4(),
        "fighter2_id": uuid4(),
        "fight_order": 1,
        "fight_type": "main",
        "weight_class": "Lightweight",
        "rounds": 3,
        "is_title_fight": False,
    }
    defaults.update(kwargs)
    return CreateFight(**defaults)


class TestCreateEvent:
    @pytest.mark.asyncio
    async def test_creates_event_with_fights(self):
        mock_uow = MagicMock()
        mock_session = AsyncMock()
        mock_uow.get_session = AsyncMock(return_value=mock_session)

        service = EventService(
            mock_uow, MagicMock(), MagicMock(), MagicMock(), MagicMock()
        )

        payload = CreateEvent(
            name="UFC 300",
            date=datetime.now(timezone.utc),
            organization="UFC",
            location="Las Vegas",
            fights=[make_fight_create(), make_fight_create(fight_order=2)],
        )

        result = await service.create_event(payload, uuid4())

        assert result.name == "UFC 300"
        assert result.status == "scheduled"
        assert mock_session.add.call_count == 3
        mock_session.flush.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_creates_event_with_one_fight(self):
        mock_uow = MagicMock()
        mock_session = AsyncMock()
        mock_uow.get_session = AsyncMock(return_value=mock_session)

        service = EventService(
            mock_uow, MagicMock(), MagicMock(), MagicMock(), MagicMock()
        )

        payload = CreateEvent(
            name="UFC 301",
            date=datetime.now(timezone.utc),
            organization="UFC",
            location="Rio",
            fights=[make_fight_create()],
        )

        result = await service.create_event(payload, uuid4())

        assert result.name == "UFC 301"
        assert mock_session.add.call_count == 2


class TestGetEvent:
    @pytest.mark.asyncio
    async def test_returns_event_when_found(self):
        mock_repo = AsyncMock()
        event = make_event()
        mock_repo.get_with_fights = AsyncMock(return_value=event)

        service = EventService(MagicMock(), MagicMock(), mock_repo, MagicMock(), MagicMock())
        result = await service.get_event(event.id)

        assert result == event

    @pytest.mark.asyncio
    async def test_raises_not_found(self):
        mock_repo = AsyncMock()
        mock_repo.get_with_fights = AsyncMock(return_value=None)

        service = EventService(MagicMock(), MagicMock(), mock_repo, MagicMock(), MagicMock())
        with pytest.raises(NotFoundError):
            await service.get_event(uuid4())


class TestListEvents:
    @pytest.mark.asyncio
    async def test_delegates_to_repo_with_filters(self):
        mock_repo = AsyncMock()
        mock_repo.list_events = AsyncMock(return_value=[])

        service = EventService(MagicMock(), MagicMock(), mock_repo, MagicMock(), MagicMock())
        await service.list_events(
            skip=10, limit=20, status="scheduled", organization="UFC",
            search="Jones", order_by="date",
        )

        mock_repo.list_events.assert_called_once_with(
            skip=10, limit=20, status="scheduled", organization="UFC",
            search="Jones", order_by="date",
        )


class TestAddFightToEvent:
    @pytest.mark.asyncio
    async def test_adds_fight_to_scheduled_event(self):
        mock_uow = MagicMock()
        mock_session = AsyncMock()
        mock_uow.get_session = AsyncMock(return_value=mock_session)

        mock_repo = AsyncMock()
        event = make_event(status="scheduled")
        mock_repo.get_by_id = AsyncMock(return_value=event)

        service = EventService(
            mock_uow, MagicMock(), mock_repo, MagicMock(), MagicMock()
        )

        fight_data = AddFightToEvent(
            fighter1_id=uuid4(), fighter2_id=uuid4(),
            fight_order=1, fight_type="main",
        )
        result = await service.add_fight_to_event(event.id, fight_data)

        assert isinstance(result, Fight)
        assert result.event_id == event.id
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_raises_when_event_not_found(self):
        mock_repo = AsyncMock()
        mock_repo.get_by_id = AsyncMock(return_value=None)

        service = EventService(
            MagicMock(), MagicMock(), mock_repo, MagicMock(), MagicMock()
        )

        with pytest.raises(NotFoundError):
            await service.add_fight_to_event(uuid4(), MagicMock())

    @pytest.mark.asyncio
    async def test_raises_when_event_not_scheduled(self):
        mock_repo = AsyncMock()
        event = make_event(status="completed")
        mock_repo.get_by_id = AsyncMock(return_value=event)

        service = EventService(
            MagicMock(), MagicMock(), mock_repo, MagicMock(), MagicMock()
        )

        with pytest.raises(ForbiddenError):
            await service.add_fight_to_event(event.id, MagicMock())


class TestDeleteEvent:
    @pytest.mark.asyncio
    async def test_deletes_event(self):
        mock_repo = AsyncMock()
        mock_repo.delete = AsyncMock(return_value=True)

        service = EventService(MagicMock(), MagicMock(), mock_repo, MagicMock(), MagicMock())
        result = await service.delete_event(uuid4())

        assert result is True
        mock_repo.delete.assert_called_once()
