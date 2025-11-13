"""
Teste End-to-End da Integração do Modelo ML

Este script testa o fluxo completo:
1. Carregamento do modelo
2. Busca de lutadores reais (Jon Jones vs Thiago Santos)
3. Predição ML
4. Comparação com método legado
"""

import asyncio
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.settings import get_settings
from app.database.models.base import Fighter
from app.database.repositories.fight_simulation import FightSimulationRepository
from app.database.repositories.fighter import FighterRepository
from app.database.unit_of_work import UnitOfWorkConnection
from app.services.domain.fight_simulation import FightSimulationService
from app.services.ml.model_loader import ml_model_loader
from app.services.ml.prediction_service import ml_prediction_service

settings = get_settings()


async def test_ml_integration():
    """Teste completo da integração ML"""

    print("\n" + "=" * 80)
    print("🤖 TESTE END-TO-END: INTEGRAÇÃO MODELO ML")
    print("=" * 80 + "\n")

    # 1. Carrega modelo
    print("📦 Passo 1: Carregando modelo ML...")
    model = ml_model_loader.load_model()

    if model is None:
        print("❌ FALHA: Modelo não foi carregado")
        print("Verifique:")
        print("  - service_account.json está no diretório raiz")
        print("  - Credenciais GCS estão corretas")
        print("  - gs://fight-base-ml/models/mma_model_v1.joblib existe")
        return False

    print(f"✅ Modelo carregado: {type(model).__name__}")
    print(f"   Features esperadas: {model.n_features_in_}")
    print()

    # 2. Conecta ao banco
    print("🔌 Passo 2: Conectando ao banco de dados...")

    async with UnitOfWorkConnection() as uow:
        session = await uow.get_session()
        fighter_repo = FighterRepository(session)  # 3. Busca lutadores reais
        print("🔍 Passo 3: Buscando lutadores para teste...")

        # Busca Jon Jones e Thiago Santos (luta clássica UFC 239)
        jon_jones = await fighter_repo.get_by_name("Jon Jones")
        thiago_santos = await fighter_repo.get_by_name("Thiago Santos")

        if not jon_jones or not thiago_santos:
            print("⚠️  Lutadores de teste não encontrados, usando primeiros do banco...")
            fighters = await fighter_repo.list(limit=2)
            if len(fighters) < 2:
                print("❌ FALHA: Banco precisa ter pelo menos 2 lutadores")
                return False
            fighter1, fighter2 = fighters[0], fighters[1]
        else:
            fighter1, fighter2 = jon_jones, thiago_santos

        print(f"   Fighter 1: {fighter1.name}")
        print(f"   Fighter 2: {fighter2.name}")
        print()

        # 4. Exibe estatísticas dos lutadores
        print("📊 Passo 4: Estatísticas dos lutadores")
        print("-" * 80)

        def print_fighter_stats(f: Fighter):
            print(f"   {f.name}:")
            print(f"     Record: {f.wins}-{f.losses}-{f.draws}")
            print(f"     Weight Class: {f.actual_weight_class or 'N/A'}")
            print("     ML Stats:")
            print(f"       SLPM: {f.slpm or 'N/A'} | Str Acc: {f.str_acc or 'N/A'}%")
            print(f"       SAPM: {f.sapm or 'N/A'} | Str Def: {f.str_def or 'N/A'}%")
            print(f"       TD Avg: {f.td_avg or 'N/A'} | TD Acc: {f.td_acc or 'N/A'}%")
            print(
                f"       TD Def: {f.td_def or 'N/A'}% | Sub Avg: {f.sub_avg or 'N/A'}"
            )

            # Atributos legados (DEPRECATED)
            if f.striking and f.grappling:
                print("     Legacy Attrs (DEPRECATED):")
                print(f"       Striking: {f.striking} | Grappling: {f.grappling}")
                print(f"       Defense: {f.defense} | Stamina: {f.stamina}")

        print_fighter_stats(fighter1)
        print()
        print_fighter_stats(fighter2)
        print()

        # 5. Teste de predição ML direta
        print("🤖 Passo 5: Predição ML Direta")
        print("-" * 80)

        ml_prob = ml_prediction_service.predict_winner_from_model(fighter1, fighter2)

        if ml_prob is None:
            print("❌ FALHA: Predição ML retornou None")
            return False

        print(f"   Probabilidade {fighter1.name}: {ml_prob:.2%}")
        print(f"   Probabilidade {fighter2.name}: {(1 - ml_prob):.2%}")
        print()

        # 6. Teste via FightSimulationService
        print("⚔️  Passo 6: Predição via FightSimulationService")
        print("-" * 80)

        sim_repo = FightSimulationRepository(session)
        sim_service = FightSimulationService(fighter_repo, sim_repo)

        prediction = await sim_service.predict_fight(fighter1.id, fighter2.id)

        print(
            f"   {prediction['fighter1_name']}: {prediction['fighter1_win_probability']:.2f}%"
        )
        print(
            f"   {prediction['fighter2_name']}: {prediction['fighter2_win_probability']:.2f}%"
        )
        print(f"   Striking Advantage: {prediction['striking_advantage']}")
        print(f"   Grappling Advantage: {prediction['grappling_advantage']}")
        print(f"   Analysis: {prediction['analysis']}")
        print()

        # 7. Teste de simulação completa
        print("🥊 Passo 7: Simulação Completa de Luta")
        print("-" * 80)

        simulation = await sim_service.simulate_fight(
            fighter1_id=fighter1.id,
            fighter2_id=fighter2.id,
            rounds=5,
            notes="Teste E2E - Integração ML",
            created_by="test_script",
        )

        print(
            f"   Vencedor: {fighter1.name if simulation.winner_id == fighter1.id else fighter2.name}"
        )
        print(f"   Resultado: {simulation.result_type}")
        print(f"   Rounds: {simulation.rounds}")
        if simulation.finish_round:
            print(f"   Finalizado no round: {simulation.finish_round}")
        print("   Probabilidades ML:")
        print(f"     {fighter1.name}: {simulation.fighter1_probability:.2f}%")
        print(f"     {fighter2.name}: {simulation.fighter2_probability:.2f}%")
        print()

        # 8. Validações finais
        print("✅ Passo 8: Validações")
        print("-" * 80)

        checks = [
            ("Modelo carregado", model is not None),
            ("Predição ML funcionando", ml_prob is not None),
            (
                "Probabilidades somam 100%",
                abs(
                    (simulation.fighter1_probability + simulation.fighter2_probability)
                    - 100.0
                )
                < 0.01,
            ),
            ("Simulação salva no banco", simulation.id is not None),
            ("Vencedor definido", simulation.winner_id is not None),
            (
                "Tipo de resultado válido",
                simulation.result_type in ["KO", "Submission", "Decision"],
            ),
        ]

        all_passed = True
        for check_name, check_result in checks:
            status = "✅" if check_result else "❌"
            print(f"   {status} {check_name}")
            if not check_result:
                all_passed = False

        print()
        print("=" * 80)
        if all_passed:
            print("✅ TODOS OS TESTES PASSARAM!")
            print("🎉 Sistema está pronto para usar predições ML!")
        else:
            print("❌ ALGUNS TESTES FALHARAM")
            print("Revise os erros acima e tente novamente")
        print("=" * 80)
        print()

        return all_passed


if __name__ == "__main__":
    try:
        success = asyncio.run(test_ml_integration())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERRO CRÍTICO: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
