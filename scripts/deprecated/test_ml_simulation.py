"""
Script para testar a simulação com stats de ML
"""

import asyncio
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database.models.base import Fighter
from app.services.domain.fight_simulation import FightSimulationService


def create_test_fighter(
    name: str,
    slpm: float,
    sapm: float,
    td_avg: float,
    sub_avg: float,
    str_def: float,
    td_def: float,
) -> Fighter:
    """Cria um lutador de teste com stats de ML"""
    fighter = Fighter(
        name=name,
        last_organization_fight="UFC",
        actual_weight_class="Lightweight",
        fighting_style="Striker",
        # Atributos gamificados (não usados mais na simulação, mas mantidos para UI)
        striking=80,
        grappling=70,
        defense=75,
        stamina=80,
        speed=85,
        strategy=75,
        # Stats de ML (usados na simulação)
        slpm=slpm,
        sapm=sapm,
        td_avg=td_avg,
        sub_avg=sub_avg,
        str_def=str_def,
        td_def=td_def,
        str_acc=45.0,
        td_acc=40.0,
        wins=15,
        losses=3,
        draws=0,
    )
    # Simula ID para teste
    from uuid import uuid4

    fighter.id = uuid4()
    return fighter


async def test_ml_simulation():
    """Testa a simulação usando stats de ML"""
    print("=" * 80)
    print("🥊 TESTE DE SIMULAÇÃO COM STATS DE ML")
    print("=" * 80)

    # Cria dois lutadores com stats diferentes
    # Striker forte (alto SLPM, baixo SAPM)
    striker = create_test_fighter(
        name="John Striker",
        slpm=5.5,  # Alto volume de golpes
        sapm=2.8,  # Boa defesa
        td_avg=0.5,  # Poucas quedas
        sub_avg=0.2,  # Poucas finalizações
        str_def=62.0,  # Boa defesa de striking
        td_def=75.0,  # Excelente defesa de queda
    )

    # Grappler forte (alto TD_AVG, alto SUB_AVG)
    grappler = create_test_fighter(
        name="Mike Grappler",
        slpm=3.2,  # Menos golpes
        sapm=4.1,  # Absorve mais golpes
        td_avg=3.5,  # Muitas quedas
        sub_avg=1.8,  # Muitas finalizações
        str_def=48.0,  # Defesa menor
        td_def=55.0,  # Defesa de queda menor
    )

    print(f"\n📊 Lutador 1: {striker.name}")
    print(f"   SLPM: {striker.slpm} | SAPM: {striker.sapm} | TD_AVG: {striker.td_avg}")
    print(
        f"   SUB_AVG: {striker.sub_avg} | STR_DEF: {striker.str_def}% | TD_DEF: {striker.td_def}%"
    )

    print(f"\n📊 Lutador 2: {grappler.name}")
    print(
        f"   SLPM: {grappler.slpm} | SAPM: {grappler.sapm} | TD_AVG: {grappler.td_avg}"
    )
    print(
        f"   SUB_AVG: {grappler.sub_avg} | STR_DEF: {grappler.str_def}% | TD_DEF: {grappler.td_def}%"
    )

    # Mock do serviço (não precisa de banco para teste)
    class MockService:
        def calculate_win_probability(self, f1, f2):
            # Usa o método real do serviço
            service = FightSimulationService(None, None)
            return service.calculate_win_probability(f1, f2)

        def _simulate_round(self, f1, f2, round_num):
            service = FightSimulationService(None, None)
            return service._simulate_round(f1, f2, round_num)

    service = MockService()

    # Calcula probabilidades
    prob1, prob2 = service.calculate_win_probability(striker, grappler)

    print("\n🎲 Probabilidades (via ML Model):")
    print(f"   {striker.name}: {prob1}%")
    print(f"   {grappler.name}: {prob2}%")

    # Simula 5 rounds
    print("\n🥊 Simulando 5 Rounds:")
    print("-" * 80)

    total_striker = 0
    total_grappler = 0

    for round_num in range(1, 6):
        round_result = service._simulate_round(striker, grappler, round_num)

        print(f"\n   Round {round_num}:")
        print(f"   {striker.name}: {round_result['fighter1_points']} pontos")
        print(f"   {grappler.name}: {round_result['fighter2_points']} pontos")
        print(f"   Dominante: {round_result['dominant_fighter']}")
        if round_result["events"]:
            print(f"   Eventos: {', '.join(round_result['events'])}")

        total_striker += round_result["fighter1_points"]
        total_grappler += round_result["fighter2_points"]

    print("\n" + "=" * 80)
    print("📊 RESULTADO FINAL:")
    print(f"   {striker.name}: {total_striker:.2f} pontos totais")
    print(f"   {grappler.name}: {total_grappler:.2f} pontos totais")

    winner = striker.name if total_striker > total_grappler else grappler.name
    print(f"\n🏆 VENCEDOR: {winner}")
    print("=" * 80)

    # Verifica consistência
    print("\n✅ VERIFICAÇÃO DE CONSISTÊNCIA:")
    ml_favorite = striker.name if prob1 > prob2 else grappler.name
    sim_winner = winner

    if ml_favorite == sim_winner:
        print(f"   ✓ Favorito do ML ({ml_favorite}) venceu a simulação!")
        print("   ✓ Simulação CONSISTENTE com probabilidades do modelo ML")
    else:
        print(f"   ⚠ Favorito do ML ({ml_favorite}) perdeu para {sim_winner}")
        print(
            "   ⚠ Isso pode acontecer devido à aleatoriedade (upset), mas deve ser raro"
        )

    print("\n" + "=" * 80)


if __name__ == "__main__":
    asyncio.run(test_ml_simulation())
