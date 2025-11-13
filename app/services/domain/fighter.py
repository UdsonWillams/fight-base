"""Serviço de domínio para gerenciar lutadores"""

from typing import Optional
from uuid import UUID

from app.database.models.base import Fighter
from app.database.repositories.fighter import FighterRepository
from app.exceptions.exceptions import ForbiddenError, NotFoundError
from app.schemas.domain.fighters.input import (
    FighterCreateInput,
    FighterSearchInput,
    FighterUpdateInput,
)


def _estimate_ml_stats_from_attributes(
    striking: int,
    grappling: int,
    defense: int,
    stamina: int,
    speed: int,
    submission_wins: int = 0,
    total_fights: int = 1,
) -> dict:
    """
    Estima estatísticas ML baseadas nos atributos gamificados (0-100)

    Fórmulas baseadas em análise do dataset UFC:
    - SLPM médio: ~4.0 (range 0-10)
    - Str Acc médio: ~45% (range 20-70%)
    - SAPM médio: ~3.5 (range 0-10)
    - Str Def médio: ~55% (range 30-80%)
    - TD Avg médio: ~1.5 (range 0-6)
    - TD Acc médio: ~40% (range 0-80%)
    - TD Def médio: ~60% (range 30-90%)
    - Sub Avg médio: ~0.5 (range 0-3)
    """

    # SLPM: Striking influencia diretamente (0-10 range, média ~4)
    slpm = (striking / 100) * 8.0

    # Str Acc: Combinação de striking e strategy (20-70% range, média ~45%)
    str_acc = 25.0 + (striking * 0.3) + (speed * 0.15)

    # SAPM: Inverso de defense (0-10 range, média ~3.5)
    sapm = 8.0 - (defense / 100) * 6.0

    # Str Def: Defense influencia diretamente (30-80% range, média ~55%)
    str_def = 30.0 + (defense * 0.5)

    # TD Avg: Grappling influencia (0-6 range, média ~1.5)
    td_avg = (grappling / 100) * 5.0

    # TD Acc: Grappling e strategy (0-80% range, média ~40%)
    td_acc = 15.0 + (grappling * 0.35) + (stamina * 0.15)

    # TD Def: Defense e grappling (30-90% range, média ~60%)
    td_def = 30.0 + (defense * 0.3) + (grappling * 0.2)

    # Sub Avg: Baseado em submission_wins e grappling (0-3 range, média ~0.5)
    sub_rate = (submission_wins / max(total_fights, 1)) * 100
    sub_avg = (grappling / 100) * 2.0 + (sub_rate / 100) * 1.0

    return {
        "slpm": round(slpm, 2),
        "str_acc": round(min(str_acc, 100.0), 2),
        "sapm": round(sapm, 2),
        "str_def": round(min(str_def, 100.0), 2),
        "td_avg": round(td_avg, 2),
        "td_acc": round(min(td_acc, 100.0), 2),
        "td_def": round(min(td_def, 100.0), 2),
        "sub_avg": round(min(sub_avg, 5.0), 2),
    }


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
            raise ForbiddenError(f"Fighter with name '{data.name}' already exists")

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
            raise ForbiddenError("All attributes must be between 0 and 100")

        # Estimar estatísticas ML se não fornecidas
        total_fights = (data.wins or 0) + (data.losses or 0) + (data.draws or 0)
        ml_stats = _estimate_ml_stats_from_attributes(
            striking=data.striking,
            grappling=data.grappling,
            defense=data.defense,
            stamina=data.stamina,
            speed=data.speed,
            submission_wins=data.submission_wins or 0,
            total_fights=max(total_fights, 1),
        )

        # Cria o lutador
        fighter = Fighter(
            name=data.name,
            nickname=data.nickname,
            last_organization_fight=data.last_organization_fight,
            actual_weight_class=data.actual_weight_class,
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
            weight_lbs=data.weight_lbs,
            reach_cm=data.reach_cm,
            bio=data.bio,
            image_url=data.image_url,
            is_real=data.is_real,
            # Estatísticas ML (usa fornecidas ou estimadas)
            slpm=data.slpm if data.slpm is not None else ml_stats["slpm"],
            str_acc=data.str_acc if data.str_acc is not None else ml_stats["str_acc"],
            sapm=data.sapm if data.sapm is not None else ml_stats["sapm"],
            str_def=data.str_def if data.str_def is not None else ml_stats["str_def"],
            td_avg=data.td_avg if data.td_avg is not None else ml_stats["td_avg"],
            td_acc=data.td_acc if data.td_acc is not None else ml_stats["td_acc"],
            td_def=data.td_def if data.td_def is not None else ml_stats["td_def"],
            sub_avg=data.sub_avg if data.sub_avg is not None else ml_stats["sub_avg"],
            creator_id=creator_id,
            created_by=created_by,
        )

        return await self.fighter_repo.create(fighter)

    async def get_fighter(self, fighter_id: UUID) -> Fighter:
        """Busca um lutador por ID"""
        fighter = await self.fighter_repo.get_by_id(fighter_id)
        if not fighter:
            raise NotFoundError("Fighter not found")
        return fighter

    async def update_fighter(
        self, fighter_id: UUID, data: FighterUpdateInput, updated_by: str = "system"
    ) -> Fighter:
        """Atualiza um lutador"""

        # Verifica se lutador existe
        existing = await self.fighter_repo.get_by_id(fighter_id)
        if not existing:
            raise NotFoundError("Fighter not found")

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
                    raise ForbiddenError(f"{attr} must be between 0 and 100")

        # Se atributos gamificados foram atualizados mas ML stats não foram fornecidos,
        # recalcular ML stats automaticamente
        gamified_attrs_updated = any(
            attr in update_data for attr in attributes_to_check
        )
        ml_attrs = [
            "slpm",
            "str_acc",
            "sapm",
            "str_def",
            "td_avg",
            "td_acc",
            "td_def",
            "sub_avg",
        ]
        ml_attrs_provided = any(attr in update_data for attr in ml_attrs)

        if gamified_attrs_updated and not ml_attrs_provided:
            # Usar valores atualizados ou existentes
            striking = update_data.get("striking", existing.striking)
            grappling = update_data.get("grappling", existing.grappling)
            defense = update_data.get("defense", existing.defense)
            stamina = update_data.get("stamina", existing.stamina)
            speed = update_data.get("speed", existing.speed)
            submission_wins = update_data.get(
                "submission_wins", existing.submission_wins or 0
            )
            wins = update_data.get("wins", existing.wins or 0)
            losses = update_data.get("losses", existing.losses or 0)
            draws = update_data.get("draws", existing.draws or 0)
            total_fights = max(wins + losses + draws, 1)

            ml_stats = _estimate_ml_stats_from_attributes(
                striking=striking,
                grappling=grappling,
                defense=defense,
                stamina=stamina,
                speed=speed,
                submission_wins=submission_wins,
                total_fights=total_fights,
            )

            # Adicionar ML stats recalculados ao update
            update_data.update(ml_stats)

        # Atualiza
        updated = await self.fighter_repo.update(fighter_id, update_data, updated_by)

        if not updated:
            raise NotFoundError("Fighter not found")

        return updated

    async def delete_fighter(
        self, fighter_id: UUID, deleted_by: str = "system"
    ) -> bool:
        """Remove um lutador (soft delete)"""
        success = await self.fighter_repo.delete(fighter_id, deleted_by)
        if not success:
            raise NotFoundError("Fighter not found")
        return success

    async def search_fighters(self, search_params: FighterSearchInput) -> list[Fighter]:
        """Busca lutadores com filtros"""
        return await self.fighter_repo.search_fighters(
            name=search_params.name,
            last_organization_fight=search_params.last_organization_fight,
            actual_weight_class=search_params.actual_weight_class,
            fighting_style=search_params.fighting_style,
            is_real=search_params.is_real,
            min_overall=search_params.min_overall,
            limit=search_params.limit,
            offset=search_params.offset,
        )

    async def get_total_fighters(self, search_params: FighterSearchInput) -> int:
        """Retorna o total de lutadores que correspondem aos filtros"""
        return await self.fighter_repo.count_fighters(
            name=search_params.name,
            last_organization_fight=search_params.last_organization_fight,
            actual_weight_class=search_params.actual_weight_class,
            fighting_style=search_params.fighting_style,
            is_real=search_params.is_real,
            min_overall=search_params.min_overall,
        )

    async def get_top_fighters(
        self,
        last_organization_fight: Optional[str] = None,
        actual_weight_class: Optional[str] = None,
        limit: int = 10,
    ) -> list[Fighter]:
        """Retorna os melhores lutadores"""
        return await self.fighter_repo.get_top_fighters(
            last_organization_fight=last_organization_fight,
            actual_weight_class=actual_weight_class,
            limit=limit,
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
