"""Serviço de domínio para gerenciar lutadores"""

from typing import Optional
from uuid import UUID

from app.database.models.base import Fighter
from app.database.repositories.fighter import FighterRepository
from app.exceptions.exceptions import BusinessRuleViolation, NotFound
from app.schemas.domain.fighters.input import (
    FighterCreateInput,
    FighterSearchInput,
    FighterUpdateInput,
)


class FighterService:
    """Serviço para gerenciar lutadores"""

    def __init__(self, fighter_repo: FighterRepository):
        self.fighter_repo = fighter_repo

    async def create_fighter(
        self, data: FighterCreateInput, creator_id: UUID, created_by: str = "system"
    ) -> Fighter:
        """Cria um novo lutador"""

        # Valida se já existe lutador com o mesmo nome
        existing = await self.fighter_repo.get_by_name(data.name)
        if existing:
            raise BusinessRuleViolation(
                f"Fighter with name '{data.name}' already exists"
            )

        # Valida atributos (devem estar entre 0-100)
        attributes = [
            data.striking,
            data.grappling,
            data.defense,
            data.stamina,
            data.speed,
            data.strategy,
        ]

        if any(attr < 0 or attr > 100 for attr in attributes):
            raise BusinessRuleViolation("All attributes must be between 0 and 100")

        # Cria o lutador
        fighter = Fighter(
            name=data.name,
            nickname=data.nickname,
            organization=data.organization,
            weight_class=data.weight_class,
            fighting_style=data.fighting_style,
            striking=data.striking,
            grappling=data.grappling,
            defense=data.defense,
            stamina=data.stamina,
            speed=data.speed,
            strategy=data.strategy,
            wins=data.wins or 0,
            losses=data.losses or 0,
            draws=data.draws or 0,
            ko_wins=data.ko_wins or 0,
            submission_wins=data.submission_wins or 0,
            age=data.age,
            height_cm=data.height_cm,
            reach_cm=data.reach_cm,
            bio=data.bio,
            image_url=data.image_url,
            is_real=data.is_real,
            creator_id=creator_id,
            created_by=created_by,
        )

        return await self.fighter_repo.create(fighter)

    async def get_fighter(self, fighter_id: UUID) -> Fighter:
        """Busca um lutador por ID"""
        fighter = await self.fighter_repo.get_by_id(fighter_id)
        if not fighter:
            raise NotFound("Fighter not found")
        return fighter

    async def update_fighter(
        self, fighter_id: UUID, data: FighterUpdateInput, updated_by: str = "system"
    ) -> Fighter:
        """Atualiza um lutador"""

        # Verifica se lutador existe
        existing = await self.fighter_repo.get_by_id(fighter_id)
        if not existing:
            raise NotFound("Fighter not found")

        # Prepara dados para atualização (apenas campos não-None)
        update_data = data.model_dump(exclude_unset=True, exclude_none=True)

        # Valida atributos se foram fornecidos
        attributes_to_check = [
            "striking",
            "grappling",
            "defense",
            "stamina",
            "speed",
            "strategy",
        ]

        for attr in attributes_to_check:
            if attr in update_data:
                value = update_data[attr]
                if value < 0 or value > 100:
                    raise BusinessRuleViolation(f"{attr} must be between 0 and 100")

        # Atualiza
        updated = await self.fighter_repo.update(fighter_id, update_data, updated_by)

        if not updated:
            raise NotFound("Fighter not found")

        return updated

    async def delete_fighter(
        self, fighter_id: UUID, deleted_by: str = "system"
    ) -> bool:
        """Remove um lutador (soft delete)"""
        success = await self.fighter_repo.delete(fighter_id, deleted_by)
        if not success:
            raise NotFound("Fighter not found")
        return success

    async def search_fighters(self, search_params: FighterSearchInput) -> list[Fighter]:
        """Busca lutadores com filtros"""
        return await self.fighter_repo.search_fighters(
            name=search_params.name,
            organization=search_params.organization,
            weight_class=search_params.weight_class,
            fighting_style=search_params.fighting_style,
            is_real=search_params.is_real,
            min_overall=search_params.min_overall,
            limit=search_params.limit,
            offset=search_params.offset,
        )

    async def get_top_fighters(
        self,
        organization: Optional[str] = None,
        weight_class: Optional[str] = None,
        limit: int = 10,
    ) -> list[Fighter]:
        """Retorna os melhores lutadores"""
        return await self.fighter_repo.get_top_fighters(
            organization=organization, weight_class=weight_class, limit=limit
        )

    async def get_fighter_stats(self) -> dict:
        """Retorna estatísticas gerais sobre lutadores"""
        return await self.fighter_repo.get_stats()

    async def get_fighters_by_creator(
        self, creator_id: UUID, limit: int = 50, offset: int = 0
    ) -> list[Fighter]:
        """Retorna lutadores criados por um usuário"""
        return await self.fighter_repo.get_fighters_by_creator(
            creator_id=creator_id, limit=limit, offset=offset
        )
