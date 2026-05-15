#!/usr/bin/env python3
"""
Script para testar se lutadores customizados agora funcionam com ML
"""

import asyncio
import sys
from pathlib import Path

# Adicionar raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database.models.base import Fighter
from app.database.repositories.fighter import FighterRepository
from app.database.unit_of_work import UnitOfWorkConnection
from app.services.ml.prediction_service import ml_prediction_service


async def test_custom_fighter_ml():
    """Testa se lutador customizado funciona com predição ML"""

    print("\n" + "=" * 80)
    print("🧪 TESTE: Lutador Customizado com Predição ML")
    print("=" * 80 + "\n")

    async with UnitOfWorkConnection() as uow:
        fighter_repo = FighterRepository(uow)

        # 1. Criar lutador customizado com atributos gamificados
        print(
            "🎮 Passo 1: Criando lutador customizado (apenas atributos gamificados)..."
        )
        print("-" * 80)

        custom_fighter = Fighter(
            name="Test Custom Fighter",
            nickname="The Algorithm",
            last_organization_fight="Custom",
            actual_weight_class="Lightweight",
            fighting_style="Hybrid",
            # Atributos gamificados (0-100)
            striking=85,
            grappling=75,
            defense=80,
            stamina=90,
            speed=88,
            strategy=82,
            # Estatísticas básicas
            wins=12,
            losses=3,
            draws=0,
            ko_wins=5,
            submission_wins=3,
            # Físico
            height_cm=180.0,
            weight_lbs=155.0,
            reach_cm=180.0,
            # Nota: NÃO fornecendo ML stats (slpm, td_avg, etc)
            is_real=False,
            created_by="test",
        )

        await fighter_repo.create(custom_fighter)
        print(f"✅ Lutador criado: {custom_fighter.name}")
        print(f"   ID: {custom_fighter.id}")
        print()

        # 2. Verificar se ML stats foram calculados automaticamente
        print("📊 Passo 2: Verificando ML stats calculados automaticamente...")
        print("-" * 80)

        ml_stats = {
            "SLPM": custom_fighter.slpm,
            "Str Acc": custom_fighter.str_acc,
            "SAPM": custom_fighter.sapm,
            "Str Def": custom_fighter.str_def,
            "TD Avg": custom_fighter.td_avg,
            "TD Acc": custom_fighter.td_acc,
            "TD Def": custom_fighter.td_def,
            "Sub Avg": custom_fighter.sub_avg,
        }

        all_calculated = all(v is not None for v in ml_stats.values())

        if all_calculated:
            print("✅ Todos os ML stats foram calculados:")
            for stat, value in ml_stats.items():
                print(f"   {stat}: {value}")
            print()
        else:
            print("❌ FALHA: Alguns ML stats estão None:")
            for stat, value in ml_stats.items():
                status = "✅" if value is not None else "❌"
                print(f"   {status} {stat}: {value}")
            print()
            return False

        # 3. Buscar um lutador real para comparação
        print("🔍 Passo 3: Buscando lutador real para comparação...")
        print("-" * 80)

        real_fighter = await fighter_repo.get_by_name("Jon Jones")
        if not real_fighter:
            print("⚠️  Jon Jones não encontrado, buscando qualquer lutador real...")
            fighters = await fighter_repo.list(limit=1)
            if not fighters:
                print("❌ FALHA: Nenhum lutador real no banco")
                return False
            real_fighter = fighters[0]

        print(f"✅ Lutador real selecionado: {real_fighter.name}")
        print()

        # 4. Testar predição ML
        print("🤖 Passo 4: Testando predição ML...")
        print("-" * 80)

        ml_prob = ml_prediction_service.predict_winner_from_model(
            custom_fighter, real_fighter
        )

        if ml_prob is None:
            print("❌ FALHA: Predição ML retornou None")
            return False

        print("✅ Predição ML funcionou!")
        print(f"   {custom_fighter.name}: {ml_prob:.2%}")
        print(f"   {real_fighter.name}: {(1 - ml_prob):.2%}")
        print()

        # 5. Verificar se features não são todas zero
        print("🔬 Passo 5: Verificando features ML (não devem ser todas zero)...")
        print("-" * 80)

        features = ml_prediction_service._calculate_feature_differences(
            custom_fighter, real_fighter
        )

        non_zero_features = sum(1 for v in features.values() if abs(v) > 0.001)
        total_features = len(features)

        print(f"   Features não-zero: {non_zero_features}/{total_features}")

        if (
            non_zero_features >= 6
        ):  # Pelo menos 6 das 11 features devem ser diferentes de zero
            print("✅ Features ML estão sendo calculadas corretamente")
            print("\n   Detalhes das features:")
            for feat, value in features.items():
                print(f"     {feat}: {value:.2f}")
            print()
        else:
            print("❌ FALHA: Muitas features estão zeradas (problema com cálculo)")
            print("\n   Detalhes das features:")
            for feat, value in features.items():
                status = "✅" if abs(value) > 0.001 else "❌"
                print(f"     {status} {feat}: {value:.2f}")
            print()
            return False

        # 6. Cleanup
        print("🧹 Passo 6: Limpando dados de teste...")
        print("-" * 80)
        await fighter_repo.delete(custom_fighter.id, "test")
        print("✅ Lutador de teste removido")
        print()

        print("=" * 80)
        print("✅ TESTE CONCLUÍDO COM SUCESSO!")
        print("=" * 80)
        print()
        print("📋 Resumo:")
        print("   ✅ Lutador customizado criado com atributos gamificados")
        print("   ✅ ML stats calculados automaticamente")
        print("   ✅ Predição ML funcionou corretamente")
        print("   ✅ Features não estão zeradas")
        print()
        return True


if __name__ == "__main__":
    success = asyncio.run(test_custom_fighter_ml())
    sys.exit(0 if success else 1)
