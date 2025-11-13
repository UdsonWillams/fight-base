"""ML Prediction Service - Predição de lutas usando modelo treinado"""

from typing import Optional

import pandas as pd

from app.core.logger import logger
from app.database.models.base import Fighter
from app.services.ml.model_loader import ml_model_loader


class MLPredictionService:
    """Serviço de predição usando modelo ML"""

    # Features esperadas pelo modelo (11 features - ordem EXATA do modelo treinado)
    FEATURES = [
        "height_diff",  # 1. Diferença de altura
        "weight_diff",  # 2. Diferença de peso
        "reach_diff",  # 3. Diferença de alcance
        "splm_diff",  # 4. Diferença de golpes significativos por minuto (typo no modelo original)
        "sapm_diff",  # 5. Diferença de golpes absorvidos por minuto
        "td_def_diff",  # 6. Diferença de defesa de quedas
        "td_avg_diff",  # 7. Diferença de quedas por luta
        "sub_avg_diff",  # 8. Diferença de finalizações por luta
        "str_acc_diff",  # 9. Diferença de precisão de golpes
        "wins_diff",  # 10. Diferença de vitórias
        "losses_diff",  # 11. Diferença de derrotas
    ]

    @staticmethod
    def _calculate_feature_differences(fighter1: Fighter, fighter2: Fighter) -> dict:
        """Calcula diferenças das features entre lutadores"""

        def safe_subtract(val1: Optional[float], val2: Optional[float]) -> float:
            """Subtração segura com fallback para 0"""
            v1 = val1 if val1 is not None else 0.0
            v2 = val2 if val2 is not None else 0.0
            return v1 - v2

        # Retorna apenas as 11 features que o modelo espera (na ordem correta)
        return {
            "height_diff": safe_subtract(fighter1.height_cm, fighter2.height_cm),
            "weight_diff": safe_subtract(fighter1.weight_lbs, fighter2.weight_lbs),
            "reach_diff": safe_subtract(fighter1.reach_cm, fighter2.reach_cm),
            "splm_diff": safe_subtract(
                fighter1.slpm, fighter2.slpm
            ),  # typo do modelo original
            "sapm_diff": safe_subtract(fighter1.sapm, fighter2.sapm),
            "td_def_diff": safe_subtract(fighter1.td_def, fighter2.td_def),
            "td_avg_diff": safe_subtract(fighter1.td_avg, fighter2.td_avg),
            "sub_avg_diff": safe_subtract(fighter1.sub_avg, fighter2.sub_avg),
            "str_acc_diff": safe_subtract(fighter1.str_acc, fighter2.str_acc),
            "wins_diff": safe_subtract(
                float(fighter1.wins or 0), float(fighter2.wins or 0)
            ),
            "losses_diff": safe_subtract(
                float(fighter1.losses or 0), float(fighter2.losses or 0)
            ),
        }

    @staticmethod
    def predict_winner_from_model(
        fighter1: Fighter, fighter2: Fighter
    ) -> Optional[float]:
        """
        Prediz a probabilidade de fighter1 vencer usando o modelo ML

        Args:
            fighter1: Primeiro lutador
            fighter2: Segundo lutador

        Returns:
            Probabilidade de fighter1 vencer (0.0 a 1.0) ou None se modelo não disponível
        """

        # Obter modelo
        model = ml_model_loader.get_model()
        if model is None:
            logger.warning("⚠️  Modelo ML não disponível, retornando None")
            return None

        try:
            # Calcular diferenças das features
            features_dict = MLPredictionService._calculate_feature_differences(
                fighter1, fighter2
            )

            # Criar DataFrame com features na ordem correta
            X = pd.DataFrame([features_dict], columns=MLPredictionService.FEATURES)

            logger.info(f"📊 Features enviadas: {list(X.columns)}")
            if hasattr(model, "feature_names_in_"):
                logger.info(
                    f"📊 Features esperadas pelo modelo: {list(model.feature_names_in_)}"
                )

            # Predição (retorna [prob_classe_0, prob_classe_1])
            # Assumindo que classe 1 = fighter1 vence
            probabilities = model.predict_proba(X)[0]
            fighter1_win_prob = probabilities[1]

            logger.info(
                f"🤖 ML Prediction: {fighter1.name} vs {fighter2.name} = "
                f"{fighter1_win_prob:.2%} chance de {fighter1.name} vencer"
            )

            return float(fighter1_win_prob)

        except Exception as e:
            logger.error(f"❌ Erro na predição ML: {e}")
            return None


# Singleton
ml_prediction_service = MLPredictionService()
