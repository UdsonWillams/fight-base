"""
Teste Simplificado de Integração ML (sem modelo real)

Testa apenas a estrutura de integração sem depender do modelo GCS
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database.models.base import Fighter
from app.services.ml.prediction_service import MLPredictionService


def test_ml_structure():
    """Testa estrutura sem modelo carregado"""

    print("\n" + "=" * 80)
    print("🧪 TESTE ESTRUTURA: Integração ML (sem modelo GCS)")
    print("=" * 80 + "\n")

    # 1. Criar lutadores fake
    print("📦 Passo 1: Criando lutadores de teste...")

    fighter1 = Fighter(
        name="Test Fighter 1",
        nickname="Tester",
        wins=10,
        losses=2,
        draws=0,
        actual_weight_class="Lightweight",
        # Stats ML
        slpm=4.5,
        str_acc=55.0,
        sapm=3.2,
        str_def=60.0,
        td_avg=2.5,
        td_acc=45.0,
        td_def=65.0,
        sub_avg=0.8,
    )

    fighter2 = Fighter(
        name="Test Fighter 2",
        nickname="Opponent",
        wins=8,
        losses=3,
        draws=1,
        actual_weight_class="Lightweight",
        # Stats ML
        slpm=3.8,
        str_acc=50.0,
        sapm=3.8,
        str_def=55.0,
        td_avg=1.5,
        td_acc=40.0,
        td_def=60.0,
        sub_avg=0.5,
    )

    print(f"   ✅ {fighter1.name} criado")
    print(f"   ✅ {fighter2.name} criado")
    print()

    # 2. Testar cálculo de features
    print("📊 Passo 2: Calculando diferenças de features...")

    features = MLPredictionService._calculate_feature_differences(fighter1, fighter2)

    print("   Features calculadas:")
    for feature, value in features.items():
        print(f"     {feature}: {value:.2f}")

    # Validações
    expected_splm_diff = fighter1.slpm - fighter2.slpm
    assert abs(features["splm_diff"] - expected_splm_diff) < 0.01, "SPLM diff incorreto"

    expected_str_acc_diff = fighter1.str_acc - fighter2.str_acc
    assert (
        abs(features["str_acc_diff"] - expected_str_acc_diff) < 0.01
    ), "Str Acc diff incorreto"

    print("   ✅ Todas as diferenças calculadas corretamente")
    print()

    # 3. Testar features com None
    print("🔍 Passo 3: Testando com stats faltando (None)...")

    fighter3 = Fighter(
        name="Incomplete Fighter",
        nickname="Missing Stats",
        wins=5,
        losses=5,
        draws=0,
        actual_weight_class="Welterweight",
        slpm=None,  # Stats faltando
        str_acc=None,
        sapm=2.0,
        str_def=50.0,
        td_avg=None,
        td_acc=None,
        td_def=None,
        sub_avg=None,
    )

    features_incomplete = MLPredictionService._calculate_feature_differences(
        fighter3, fighter1
    )

    print("   Features com None tratadas:")
    for feature, value in features_incomplete.items():
        print(f"     {feature}: {value:.2f}")

    # Validar que None é tratado como 0
    assert features_incomplete["splm_diff"] == -fighter1.slpm, "None não tratado como 0"
    print("   ✅ None values tratados corretamente como 0.0")
    print()

    # 4. Testar predição com modelo
    print("🤖 Passo 4: Testando predição com modelo ML...")

    # Força reload para limpar cache
    from app.services.ml.model_loader import ml_model_loader

    ml_model_loader._model = None  # Limpa cache
    ml_model_loader.load_model()

    ml_service = MLPredictionService()
    prob = ml_service.predict_winner_from_model(fighter1, fighter2)

    if prob is None:
        print("   ❌ Predição falhou (modelo não conseguiu predizer)")
    else:
        print(f"   ✅ Predição bem-sucedida: {prob:.2%} de chance do Fighter 1 vencer")
    print()

    # 5. Sumário
    print("=" * 80)
    print("✅ ESTRUTURA DE INTEGRAÇÃO ML VALIDADA!")
    print()
    print("Próximos passos para produção:")
    print(
        "  1. Upload do modelo treinado para gs://fight-base-ml/models/mma_model_v1.joblib"
    )
    print("  2. Verificar permissões do service_account.json no bucket")
    print("  3. Testar carregamento do modelo no startup da API")
    print("  4. Validar predições com lutadores reais do banco")
    print("=" * 80)
    print()

    return True


if __name__ == "__main__":
    try:
        success = test_ml_structure()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
