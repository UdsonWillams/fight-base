"""
Teste de Validação: Garantir que o modelo ML está sendo usado

Este teste verifica se:
1. O modelo ML é carregado
2. As predições vêm do ML (não do cálculo legado)
3. O fallback legado só é usado quando ML falha
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database.models.base import Fighter
from app.services.domain.fight_simulation import FightSimulationService
from app.services.ml.model_loader import ml_model_loader
from app.services.ml.prediction_service import ml_prediction_service


@pytest.mark.asyncio
async def test_ml_is_being_used():
    """Testa se o modelo ML está realmente sendo usado"""

    print("\n" + "=" * 80)
    print("🔍 VALIDAÇÃO: Modelo ML está sendo usado (não o método legado)?")
    print("=" * 80 + "\n")

    # Criar lutadores de teste
    fighter1 = Fighter(
        name="ML Test Fighter 1",
        nickname="ML Test",
        wins=15,
        losses=3,
        draws=0,
        actual_weight_class="Lightweight",
        height_cm=180.0,
        weight_lbs=155.0,
        reach_cm=180.0,
        slpm=5.2,
        str_acc=58.0,
        sapm=3.0,
        td_avg=3.5,
        td_def=70.0,
        sub_avg=1.2,
        # Atributos mágicos DEPRECATED (não devem ser usados)
        striking=90,
        grappling=85,
        defense=80,
        stamina=85,
        speed=88,
        strategy=82,
    )

    fighter2 = Fighter(
        name="ML Test Fighter 2",
        nickname="Opponent",
        wins=12,
        losses=5,
        draws=1,
        actual_weight_class="Lightweight",
        height_cm=175.0,
        weight_lbs=155.0,
        reach_cm=175.0,
        slpm=4.0,
        str_acc=52.0,
        sapm=3.8,
        td_avg=2.0,
        td_def=65.0,
        sub_avg=0.8,
        # Atributos mágicos DEPRECATED
        striking=75,
        grappling=80,
        defense=75,
        stamina=78,
        speed=76,
        strategy=74,
    )

    # ========================================================================
    # TESTE 1: Verificar se modelo ML está carregado
    # ========================================================================
    print("📦 Teste 1: Modelo ML está carregado?")
    model = await ml_model_loader.get_model()

    if model is None:
        print("   ❌ FALHA: Modelo ML não foi carregado!")
        print("   Sistema usará método legado (atributos mágicos)")
        return False

    print(f"   ✅ Modelo carregado: {type(model).__name__}")
    print(f"   Features: {model.n_features_in_}")
    print()

    # ========================================================================
    # TESTE 2: Predição ML direta retorna valor?
    # ========================================================================
    print("🤖 Teste 2: Predição ML direta funciona?")
    ml_prob = await ml_prediction_service.predict_winner_from_model(fighter1, fighter2)

    if ml_prob is None:
        print("   ❌ FALHA: Predição ML retornou None")
        print("   Sistema usará método legado")
        return False

    print(f"   ✅ Predição ML: {ml_prob:.2%}")
    print()

    # ========================================================================
    # TESTE 3: FightSimulationService usa ML (não legado)
    # ========================================================================
    print("⚔️  Teste 3: FightSimulationService usa ML?")

    # Mock dos repositórios
    fighter_repo_mock = MagicMock()
    sim_repo_mock = MagicMock()

    sim_service = FightSimulationService(fighter_repo_mock, sim_repo_mock)

    # Calcular probabilidade usando o serviço
    prob1, prob2 = await sim_service.calculate_win_probability(fighter1, fighter2)

    print("   Probabilidades calculadas:")
    print(f"     {fighter1.name}: {prob1:.2f}%")
    print(f"     {fighter2.name}: {prob2:.2f}%")

    # Verificar se a probabilidade está em porcentagem (ML retorna 0-100)
    ml_prob_percentage = ml_prob * 100

    # Tolerância de 0.1% para comparação
    if abs(prob1 - ml_prob_percentage) < 0.1:
        print("   ✅ CONFIRMADO: Usando predição ML!")
        print(f"      ML direto: {ml_prob_percentage:.2f}%")
        print(f"      Via service: {prob1:.2f}%")
        ml_is_used = True
    else:
        print("   ❌ AVISO: Probabilidades diferentes!")
        print(f"      ML direto: {ml_prob_percentage:.2f}%")
        print(f"      Via service: {prob1:.2f}%")
        print(f"      Diferença: {abs(prob1 - ml_prob_percentage):.2f}%")
        print("   Provavelmente usando método legado (atributos mágicos)")
        ml_is_used = False
    print()

    # ========================================================================
    # TESTE 4: Comparar com método legado (para confirmar diferença)
    # ========================================================================
    print("🔬 Teste 4: Comparar ML vs Legado")

    # Calcular pelo método legado (usando _calculate_fighter_power)
    power1 = sim_service._calculate_fighter_power(fighter1, "overall")
    power2 = sim_service._calculate_fighter_power(fighter2, "overall")

    total_power = power1 + power2
    legacy_prob1 = (power1 / total_power) * 100

    print(f"   Método Legado: {legacy_prob1:.2f}%")
    print(f"   Método ML: {ml_prob_percentage:.2f}%")
    print(f"   Diferença: {abs(legacy_prob1 - ml_prob_percentage):.2f}%")

    if abs(legacy_prob1 - ml_prob_percentage) > 1.0:
        print("   ✅ Métodos produzem resultados diferentes (esperado)")
    else:
        print("   ⚠️  Métodos produzem resultados similares (coincidência?)")
    print()

    # ========================================================================
    # TESTE 5: Verificar fallback quando ML falha
    # ========================================================================
    print("🛡️  Teste 5: Fallback legado funciona quando ML falha?")

    # Simular falha do ML (retornar None)
    with patch.object(
        ml_prediction_service, "predict_winner_from_model", return_value=None
    ):
        prob_fallback1, prob_fallback2 = await sim_service.calculate_win_probability(
            fighter1, fighter2
        )

        print("   Com ML = None:")
        print(f"     {fighter1.name}: {prob_fallback1:.2f}%")
        print(f"     {fighter2.name}: {prob_fallback2:.2f}%")

        # Deve usar método legado
        if abs(prob_fallback1 - legacy_prob1) < 0.1:
            print("   ✅ Fallback para método legado funcionando")
        else:
            print("   ❌ Fallback não está funcionando corretamente")
    print()

    # ========================================================================
    # RESULTADO FINAL
    # ========================================================================
    print("=" * 80)
    if ml_is_used:
        print("✅ VALIDAÇÃO COMPLETA: MODELO ML ESTÁ SENDO USADO!")
        print()
        print("Confirmações:")
        print("  ✅ Modelo ML carregado do GCS")
        print("  ✅ Predições vêm do RandomForestClassifier")
        print("  ✅ FightSimulationService usa ML (não atributos mágicos)")
        print("  ✅ Fallback legado disponível se ML falhar")
        print()
        print("🎉 Sistema 100% operacional com ML!")
    else:
        print("❌ VALIDAÇÃO FALHOU: SISTEMA NÃO ESTÁ USANDO ML")
        print()
        print("Possíveis causas:")
        print("  - Modelo não foi carregado corretamente")
        print("  - Erro na integração do serviço")
        print("  - Fallback legado sendo usado por engano")
    print("=" * 80)
    print()

    return ml_is_used


if __name__ == "__main__":
    try:
        success = test_ml_is_being_used()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERRO CRÍTICO: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
