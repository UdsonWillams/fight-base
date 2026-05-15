#!/usr/bin/env python3
"""Verifica se lutadores customizados têm ML stats"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database.repositories.fighter import FighterRepository
from app.database.unit_of_work import UnitOfWorkConnection


async def check_custom_fighters():
    print("\n" + "=" * 80)
    print("🔍 VERIFICANDO LUTADORES CUSTOMIZADOS COM ML STATS")
    print("=" * 80 + "\n")

    async with UnitOfWorkConnection() as uow:
        fighter_repo = FighterRepository(uow)

        # Buscar lutadores customizados (is_real=False)
        from app.schemas.domain.fighters.input import FighterSearchInput

        search_params = FighterSearchInput(limit=10, offset=0, is_real=False)
        fighters = await fighter_repo.search_fighters(
            name=search_params.name,
            last_organization_fight=search_params.last_organization_fight,
            actual_weight_class=search_params.actual_weight_class,
            fighting_style=search_params.fighting_style,
            is_real=search_params.is_real,
            min_overall=search_params.min_overall,
            limit=search_params.limit,
            offset=search_params.offset,
        )

        if not fighters:
            print("⚠️  Nenhum lutador customizado encontrado")
            print("   Vou buscar últimos 5 lutadores criados...")
            search_params = FighterSearchInput(limit=5, offset=0)
            fighters = await fighter_repo.search_fighters(
                name=search_params.name,
                last_organization_fight=search_params.last_organization_fight,
                actual_weight_class=search_params.actual_weight_class,
                fighting_style=search_params.fighting_style,
                is_real=None,  # Buscar todos
                min_overall=search_params.min_overall,
                limit=search_params.limit,
                offset=search_params.offset,
            )

        if not fighters:
            print("❌ Nenhum lutador encontrado no banco")
            return

        for fighter in fighters:
            print(f"\n{'=' * 60}")
            print(f"Lutador: {fighter.name}")
            print(f"ID: {fighter.id}")
            print(f"Criado em: {fighter.created_at}")
            print(f"É real: {fighter.is_real}")
            print("\n📊 ML Stats:")
            print(f"   SLPM: {fighter.slpm}")
            print(f"   Str Acc: {fighter.str_acc}%")
            print(f"   SAPM: {fighter.sapm}")
            print(f"   Str Def: {fighter.str_def}%")
            print(f"   TD Avg: {fighter.td_avg}")
            print(f"   TD Acc: {fighter.td_acc}%")
            print(f"   TD Def: {fighter.td_def}%")
            print(f"   Sub Avg: {fighter.sub_avg}")
            print(f"   Weight: {fighter.weight_lbs} lbs")

            # Verificar se todos ML stats estão preenchidos
            ml_stats = [
                fighter.slpm,
                fighter.str_acc,
                fighter.sapm,
                fighter.str_def,
                fighter.td_avg,
                fighter.td_acc,
                fighter.td_def,
                fighter.sub_avg,
            ]

            filled = sum(1 for s in ml_stats if s is not None)
            print(f"\n✅ ML Stats preenchidos: {filled}/8")

            if filled == 8:
                print("✅ SUCESSO: Todos ML stats calculados!")
            else:
                print(f"⚠️  Faltam {8 - filled} ML stats")


if __name__ == "__main__":
    asyncio.run(check_custom_fighters())
