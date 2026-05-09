"""ML Prediction Service - Predição de lutas usando modelo treinado"""

from datetime import datetime, timezone
from typing import Optional

import pandas as pd

from app.core.logger import logger
from app.database.models.base import Fighter
from app.services.ml.model_loader import ml_model_loader


class MLPredictionService:
    """Serviço de predição usando modelo ML"""

    # 🎯 Features atualizadas (13 features - ordem EXATA do modelo treinado V2)
    FEATURES = [
        "height_diff",  # 1. Diferença de altura (em polegadas)
        "weight_diff",  # 2. Diferença de peso (em libras)
        "reach_diff",  # 3. Diferença de envergadura (em polegadas)
        "splm_diff",  # 4. Diferença de golpes significativos por minuto
        "sapm_diff",  # 5. Diferença de golpes absorvidos por minuto
        "td_def_diff",  # 6. Diferença de defesa de quedas
        "td_avg_diff",  # 7. Diferença de quedas por luta
        "sub_avg_diff",  # 8. Diferença de finalizações por luta
        "str_acc_diff",  # 9. Diferença de precisão de golpes
        "wins_diff",  # 10. Diferença de vitórias
        "losses_diff",  # 11. Diferença de derrotas
        "age_diff",  # 12. Diferença de Idade (Fighter1 - Fighter2)
        "is_opposite_stance",  # 13. Confronto de bases (0 = Iguais, 1 = Opostas)
    ]

    @staticmethod
    def _calculate_feature_differences(
        fighter1: Fighter, fighter2: Fighter, event_date: Optional[datetime] = None
    ) -> dict:
        """Calcula diferenças das features entre lutadores"""

        def safe_subtract(val1: Optional[float], val2: Optional[float]) -> float:
            """Subtração segura com fallback para 0"""
            v1 = float(val1) if val1 is not None else 0.0
            v2 = float(val2) if val2 is not None else 0.0
            return v1 - v2

        def calculate_age(dob: Optional[datetime], ref_date: datetime) -> float:
            """Calcula a idade do lutador na data do evento"""
            if not dob:
                return 0.0

            # Garante que ambas as datas têm ou não timezone para evitar erro de subtração
            if dob.tzinfo and not ref_date.tzinfo:
                ref_date = ref_date.replace(tzinfo=timezone.utc)
            elif not dob.tzinfo and ref_date.tzinfo:
                dob = dob.replace(tzinfo=timezone.utc)

            age_days = (ref_date - dob).days
            return age_days / 365.25

        def check_stance_matchup(stance1: Optional[str], stance2: Optional[str]) -> int:
            """Retorna 1 se forem bases opostas, 0 se forem iguais ou desconhecidas"""
            if not stance1 or not stance2:
                return 0
            s1 = str(stance1).lower().strip()
            s2 = str(stance2).lower().strip()
            if s1 in ["--", ""] or s2 in ["--", ""]:
                return 0
            return 1 if s1 != s2 else 0

        # Define a data de referência para calcular a idade
        ref_date = event_date if event_date else datetime.now(timezone.utc)

        # Calcula idades usando o datetime do SQLAlchemy
        f1_age = calculate_age(fighter1.date_of_birth, ref_date)
        f2_age = calculate_age(fighter2.date_of_birth, ref_date)

        # Retorna o dicionário na ordem estrita do modelo
        # ATENÇÃO: Usando as properties height_inches e reach_inches que você criou!
        return {
            "height_diff": safe_subtract(
                fighter1.height_inches, fighter2.height_inches
            ),
            "weight_diff": safe_subtract(fighter1.weight_lbs, fighter2.weight_lbs),
            "reach_diff": safe_subtract(fighter1.reach_inches, fighter2.reach_inches),
            "splm_diff": safe_subtract(fighter1.slpm, fighter2.slpm),
            "sapm_diff": safe_subtract(fighter1.sapm, fighter2.sapm),
            "td_def_diff": safe_subtract(fighter1.td_def, fighter2.td_def),
            "td_avg_diff": safe_subtract(fighter1.td_avg, fighter2.td_avg),
            "sub_avg_diff": safe_subtract(fighter1.sub_avg, fighter2.sub_avg),
            "str_acc_diff": safe_subtract(fighter1.str_acc, fighter2.str_acc),
            "wins_diff": safe_subtract(fighter1.wins, fighter2.wins),
            "losses_diff": safe_subtract(fighter1.losses, fighter2.losses),
            "age_diff": safe_subtract(f1_age, f2_age),
            "is_opposite_stance": check_stance_matchup(
                fighter1.stance, fighter2.stance
            ),
        }

    @staticmethod
    async def predict_winner_from_model(
        fighter1: Fighter, fighter2: Fighter, event_date: Optional[datetime] = None
    ) -> Optional[float]:
        """
        Prediz a probabilidade de fighter1 vencer usando o modelo ML.

        Args:
            fighter1: Primeiro lutador (Red Corner)
            fighter2: Segundo lutador (Blue Corner)
            event_date: Data do evento para calcular idade exata (opcional)

        Returns:
            Probabilidade de fighter1 vencer (0.0 a 1.0) ou None se falhar.
        """
        model = await ml_model_loader.get_model()
        if model is None:
            logger.warning("⚠️  Modelo ML não disponível, retornando None")
            return None

        try:
            # Calcular diferenças injetando a data do evento
            features_dict = MLPredictionService._calculate_feature_differences(
                fighter1, fighter2, event_date
            )

            # DataFrame na ordem estrita do TARGET_FEATURES
            X = pd.DataFrame([features_dict], columns=MLPredictionService.FEATURES)

            logger.info(f"📊 Features enviadas ({len(X.columns)}): {list(X.columns)}")

            # Validação preventiva
            if hasattr(model, "n_features_in_") and model.n_features_in_ != len(
                X.columns
            ):
                logger.error(
                    f"❌ Incompatibilidade: O modelo espera {model.n_features_in_} features, "
                    f"mas o serviço enviou {len(X.columns)}."
                )
                return None

            # Predição
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
