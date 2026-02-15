import secrets
import string
from typing import List, Optional
from uuid import UUID

from app.database.models.base import League, LeagueMember
from app.database.repositories.league import LeagueRepository
from app.database.unit_of_work import UnitOfWorkConnection


class LeagueService:
    def __init__(self, uow: UnitOfWorkConnection, league_repo: LeagueRepository):
        self.uow = uow
        self.league_repo = league_repo

    async def create_league(
        self,
        user_id: UUID,
        name: str,
        description: Optional[str],
        is_public: bool,
        max_members: int,
    ) -> League:
        """Cria uma nova liga e adiciona o criador como membro"""
        invite_code = self._generate_invite_code()

        league = League(
            name=name,
            description=description,
            invite_code=invite_code,
            is_public=is_public,
            max_members=max_members,
            owner_id=user_id,
            created_by=str(user_id),
            updated_by=str(user_id),
        )

        created_league = await self.league_repo.create(league)

        # Adicionar criador como membro
        member = LeagueMember(
            league_id=created_league.id,
            user_id=user_id,
            created_by=str(user_id),
            updated_by=str(user_id),
        )
        session = await self.uow.get_session()
        session.add(member)
        await session.commit()

        return created_league

    async def join_league(self, user_id: UUID, invite_code: str) -> League:
        """Entra em uma liga usando o código de convite"""
        league = await self.league_repo.get_by_invite_code(invite_code)
        if not league:
            raise ValueError("Liga não encontrada com este código.")

        # Verificar se já é membro
        existing_member = await self.league_repo.get_member(league.id, user_id)
        if existing_member:
            raise ValueError("Você já faz parte desta liga.")

        # Verificar limite de membros
        session = await self.uow.get_session()
        from sqlalchemy import func, select

        count_query = select(func.count(LeagueMember.id)).filter(
            LeagueMember.league_id == league.id
        )
        count_result = await session.execute(count_query)
        count = count_result.scalar()

        if count >= league.max_members:
            raise ValueError("Esta liga atingiu o limite máximo de membros.")

        member = LeagueMember(
            league_id=league.id,
            user_id=user_id,
            created_by=str(user_id),
            updated_by=str(user_id),
        )
        session.add(member)
        await session.commit()

        return league

    def _generate_invite_code(self, length: int = 8) -> str:
        """Gera um código aleatório alfanumérico"""
        chars = string.ascii_uppercase + string.digits
        return "".join(secrets.choice(chars) for _ in range(length))

    async def get_user_leagues(self, user_id: UUID) -> List[League]:
        return await self.league_repo.get_user_leagues(user_id)

    async def get_league_leaderboard(
        self, league_id: UUID, limit: int = 50
    ) -> List[LeagueMember]:
        return await self.league_repo.get_league_members(league_id, limit)
