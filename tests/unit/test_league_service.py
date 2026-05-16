import string
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.database.models.base import League, LeagueMember
from app.services.domain.league import LeagueService


def make_league(**kwargs):
    defaults = {
        "id": uuid4(),
        "name": "Test League",
        "description": "Test Desc",
        "invite_code": "ABC12345",
        "is_public": False,
        "max_members": 10,
        "owner_id": uuid4(),
    }
    defaults.update(kwargs)
    return League(**defaults)


class TestGenerateInviteCode:
    def test_length_is_8(self):
        service = LeagueService(MagicMock(), MagicMock())
        code = service._generate_invite_code()
        assert len(code) == 8

    def test_only_alphanumeric_uppercase(self):
        service = LeagueService(MagicMock(), MagicMock())
        code = service._generate_invite_code()
        assert code.isalnum()
        assert code == code.upper()
        valid_chars = set(string.ascii_uppercase + string.digits)
        assert all(c in valid_chars for c in code)

    def test_generates_different_codes(self):
        service = LeagueService(MagicMock(), MagicMock())
        codes = {service._generate_invite_code() for _ in range(20)}
        assert len(codes) > 1


class TestCreateLeague:
    @pytest.mark.asyncio
    async def test_creates_league_and_adds_creator_as_member(self):
        mock_uow = MagicMock()
        mock_session = AsyncMock()
        mock_uow.get_session = AsyncMock(return_value=mock_session)

        mock_repo = AsyncMock()
        created_league = make_league(name="My League")
        mock_repo.create = AsyncMock(return_value=created_league)

        service = LeagueService(mock_uow, mock_repo)
        user_id = uuid4()
        result = await service.create_league(
            user_id=user_id,
            name="My League",
            description=None,
            is_public=False,
            max_members=5,
        )

        assert result == created_league
        mock_repo.create.assert_called_once()
        mock_session.add.assert_called_once()
        added_member = mock_session.add.call_args[0][0]
        assert isinstance(added_member, LeagueMember)
        assert added_member.league_id == created_league.id
        assert added_member.user_id == user_id
        assert added_member.created_by == str(user_id)
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_generates_invite_code_automatically(self):
        mock_uow = MagicMock()
        mock_session = AsyncMock()
        mock_uow.get_session = AsyncMock(return_value=mock_session)

        mock_repo = AsyncMock()
        created_league = make_league(invite_code="GENERATED")
        mock_repo.create = AsyncMock(return_value=created_league)

        service = LeagueService(mock_uow, mock_repo)
        result = await service.create_league(
            user_id=uuid4(),
            name="Test",
            description=None,
            is_public=True,
            max_members=50,
        )

        league_arg = mock_repo.create.call_args[0][0]
        assert len(league_arg.invite_code) == 8

    @pytest.mark.asyncio
    async def test_sets_owner_id_to_user_id(self):
        mock_uow = MagicMock()
        mock_session = AsyncMock()
        mock_uow.get_session = AsyncMock(return_value=mock_session)

        mock_repo = AsyncMock()
        created_league = make_league()
        mock_repo.create = AsyncMock(return_value=created_league)

        service = LeagueService(mock_uow, mock_repo)
        user_id = uuid4()
        await service.create_league(
            user_id=user_id,
            name="Test",
            description=None,
            is_public=False,
            max_members=10,
        )

        league_arg = mock_repo.create.call_args[0][0]
        assert league_arg.owner_id == user_id
        assert league_arg.created_by == str(user_id)


class TestJoinLeague:
    @pytest.mark.asyncio
    async def test_joins_successfully(self):
        mock_uow = MagicMock()
        mock_session = AsyncMock()
        mock_uow.get_session = AsyncMock(return_value=mock_session)

        mock_repo = AsyncMock()
        league = make_league(invite_code="JOIN123", max_members=10)
        mock_repo.get_by_invite_code = AsyncMock(return_value=league)
        mock_repo.get_member = AsyncMock(return_value=None)

        mock_result = MagicMock()
        mock_result.scalar = MagicMock(return_value=3)
        mock_session.execute = AsyncMock(return_value=mock_result)

        service = LeagueService(mock_uow, mock_repo)
        user_id = uuid4()
        result = await service.join_league(user_id=user_id, invite_code="JOIN123")

        assert result == league
        mock_repo.get_by_invite_code.assert_called_once_with("JOIN123")
        mock_repo.get_member.assert_called_once_with(league.id, user_id)
        mock_session.add.assert_called_once()
        added_member = mock_session.add.call_args[0][0]
        assert isinstance(added_member, LeagueMember)
        assert added_member.league_id == league.id
        assert added_member.user_id == user_id
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_raises_when_league_not_found(self):
        mock_repo = AsyncMock()
        mock_repo.get_by_invite_code = AsyncMock(return_value=None)

        service = LeagueService(MagicMock(), mock_repo)
        with pytest.raises(ValueError, match="não encontrada"):
            await service.join_league(user_id=uuid4(), invite_code="INVALID")

    @pytest.mark.asyncio
    async def test_raises_when_already_member(self):
        mock_repo = AsyncMock()
        league = make_league()
        mock_repo.get_by_invite_code = AsyncMock(return_value=league)
        mock_repo.get_member = AsyncMock(return_value=MagicMock())

        service = LeagueService(MagicMock(), mock_repo)
        user_id = uuid4()
        with pytest.raises(ValueError, match="já faz parte"):
            await service.join_league(user_id=user_id, invite_code="JOIN123")

    @pytest.mark.asyncio
    async def test_raises_when_league_is_full(self):
        mock_uow = MagicMock()
        mock_session = AsyncMock()
        mock_uow.get_session = AsyncMock(return_value=mock_session)

        mock_repo = AsyncMock()
        league = make_league(max_members=5)
        mock_repo.get_by_invite_code = AsyncMock(return_value=league)
        mock_repo.get_member = AsyncMock(return_value=None)

        mock_result = MagicMock()
        mock_result.scalar = MagicMock(return_value=5)
        mock_session.execute = AsyncMock(return_value=mock_result)

        service = LeagueService(mock_uow, mock_repo)
        with pytest.raises(ValueError, match="limite máximo"):
            await service.join_league(user_id=uuid4(), invite_code="JOIN123")

    @pytest.mark.asyncio
    async def test_allows_join_when_one_slot_left(self):
        mock_uow = MagicMock()
        mock_session = AsyncMock()
        mock_uow.get_session = AsyncMock(return_value=mock_session)

        mock_repo = AsyncMock()
        league = make_league(max_members=5)
        mock_repo.get_by_invite_code = AsyncMock(return_value=league)
        mock_repo.get_member = AsyncMock(return_value=None)

        mock_result = MagicMock()
        mock_result.scalar = MagicMock(return_value=4)
        mock_session.execute = AsyncMock(return_value=mock_result)

        service = LeagueService(mock_uow, mock_repo)
        result = await service.join_league(user_id=uuid4(), invite_code="JOIN123")
        assert result == league


class TestGetUserLeagues:
    @pytest.mark.asyncio
    async def test_returns_leagues_for_user(self):
        mock_repo = AsyncMock()
        leagues = [make_league(), make_league()]
        mock_repo.get_user_leagues = AsyncMock(return_value=leagues)

        service = LeagueService(MagicMock(), mock_repo)
        user_id = uuid4()
        result = await service.get_user_leagues(user_id)

        assert result == leagues
        mock_repo.get_user_leagues.assert_called_once_with(user_id)


class TestGetLeagueLeaderboard:
    @pytest.mark.asyncio
    async def test_returns_leaderboard(self):
        mock_repo = AsyncMock()
        members = [MagicMock(spec=LeagueMember), MagicMock(spec=LeagueMember)]
        mock_repo.get_league_members = AsyncMock(return_value=members)

        service = LeagueService(MagicMock(), mock_repo)
        league_id = uuid4()
        result = await service.get_league_leaderboard(league_id, limit=50)

        assert result == members
        mock_repo.get_league_members.assert_called_once_with(league_id, 50)

    @pytest.mark.asyncio
    async def test_default_limit_is_50(self):
        mock_repo = AsyncMock()
        mock_repo.get_league_members = AsyncMock(return_value=[])

        service = LeagueService(MagicMock(), mock_repo)
        await service.get_league_leaderboard(uuid4())

        mock_repo.get_league_members.assert_called_once()
        args = mock_repo.get_league_members.call_args
        assert args[0][1] == 50
