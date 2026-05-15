"""ML Prediction Service - Predição de lutas usando modelo treinado"""

from datetime import datetime, timezone
from typing import Optional

import pandas as pd

from app.core.logger import logger
from app.database.models.base import Fighter
from app.services.ml.model_loader import ml_model_loader


class MLPredictionService:
    """Serviço de predição usando modelo ML"""

    # 🎯 Features V1 (18 features - modelo treinado V1)
    FEATURES = [
        "height_diff",  # 1.  Diferença de altura (em polegadas)
        "weight_diff",  # 2.  Diferença de peso (em libras)
        "reach_diff",  # 3.  Diferença de envergadura (em polegadas)
        "splm_diff",  # 4.  Diferença de golpes significativos por minuto
        "sapm_diff",  # 5.  Diferença de golpes absorvidos por minuto
        "td_def_diff",  # 6.  Diferença de defesa de quedas
        "td_avg_diff",  # 7.  Diferença de quedas por luta
        "sub_avg_diff",  # 8.  Diferença de finalizações por luta
        "str_acc_diff",  # 9.  Diferença de precisão de golpes
        "td_acc_diff",  # 10. Diferença de precisão de quedas (%)
        "win_rate_diff",  # 11. Diferença de aproveitamento de vitórias (%)
        "experience_diff",  # 12. Diferença de lutas na carreira (total_fights)
        "finish_rate_diff",  # 13. Diferença de taxa de finalização (%)
        "kd_avg_diff",  # 14. Diferença de knockdowns por luta
        "wins_diff",  # 15. Diferença de vitórias
        "losses_diff",  # 16. Diferença de derrotas
        "age_diff",  # 17. Diferença de idade (Fighter1 - Fighter2)
        "is_opposite_stance",  # 18. Confronto de bases (0 = Iguais, 1 = Opostas)
    ]

    # 🎯 Features V2 (21 features - Stacking Ensemble V2)
    FEATURES_V2 = [
        "height_diff",
        "weight_diff",
        "reach_diff",
        "splm_diff",
        "sapm_diff",
        "td_def_diff",
        "td_avg_diff",
        "sub_avg_diff",
        "str_acc_diff",
        "td_acc_diff",
        "win_rate_diff",
        "experience_diff",
        "finish_rate_diff",
        "kd_avg_diff",
        "ctrl_time_diff",  # 15. Diferença de controle por minuto (grappling)
        "reach_td_def",  # 16. Interação envergadura × defesa de queda
        "age_experience",  # 17. Interação idade × experiência
        "wins_diff",
        "losses_diff",
        "age_diff",
        "is_opposite_stance",
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
        features = {
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
            "td_acc_diff": safe_subtract(fighter1.td_acc, fighter2.td_acc),
            "win_rate_diff": safe_subtract(
                fighter1.wins / max(fighter1.wins + fighter1.losses, 1) * 100,
                fighter2.wins / max(fighter2.wins + fighter2.losses, 1) * 100,
            ),
            "experience_diff": safe_subtract(
                (fighter1.wins or 0) + (fighter1.losses or 0) + (fighter1.draws or 0),
                (fighter2.wins or 0) + (fighter2.losses or 0) + (fighter2.draws or 0),
            ),
            "finish_rate_diff": safe_subtract(
                ((fighter1.ko_wins or 0) + (fighter1.submission_wins or 0))
                / max(fighter1.wins or 1, 1)
                * 100,
                ((fighter2.ko_wins or 0) + (fighter2.submission_wins or 0))
                / max(fighter2.wins or 1, 1)
                * 100,
            ),
            "kd_avg_diff": safe_subtract(fighter1.kd_avg, fighter2.kd_avg),
            "ctrl_time_diff": safe_subtract(fighter1.ctrl_avg, fighter2.ctrl_avg),
            "reach_td_def": safe_subtract(
                fighter1.reach_inches or 0, fighter2.reach_inches or 0
            )
            * safe_subtract(fighter1.td_def, fighter2.td_def)
            / 100.0,
            "wins_diff": safe_subtract(fighter1.wins, fighter2.wins),
            "losses_diff": safe_subtract(fighter1.losses, fighter2.losses),
            "age_diff": safe_subtract(f1_age, f2_age),
            "is_opposite_stance": check_stance_matchup(
                fighter1.stance, fighter2.stance
            ),
        }

        # Interação idade × experiência
        features["age_experience"] = (
            features["age_diff"] * features["experience_diff"] / 100.0
        )
        return features

    @staticmethod
    async def predict_winner_from_model(
        fighter1: Fighter, fighter2: Fighter, event_date: Optional[datetime] = None
    ) -> Optional[float]:
        """
        Prediz a probabilidade de fighter1 vencer usando o modelo ML (V1 ou V2).

        Auto-detecta se o modelo carregado é V1 (18 features) ou V2 (21 features).
        """
        model = await ml_model_loader.get_model()
        if model is None:
            logger.warning("⚠️  Modelo ML não disponível, retornando None")
            return None

        try:
            features_dict = MLPredictionService._calculate_feature_differences(
                fighter1, fighter2, event_date
            )

            n_feat = model.n_features_in_ if hasattr(model, "n_features_in_") else 18

            if n_feat == 21:
                features_list = MLPredictionService.FEATURES_V2
                logger.info("🚀 Usando modelo V2 (Stacking Ensemble, 21 features)")
            else:
                features_list = MLPredictionService.FEATURES
                logger.info("📊 Usando modelo V1 (18 features)")

            X = pd.DataFrame([features_dict], columns=features_list)

            if hasattr(model, "n_features_in_") and model.n_features_in_ != len(
                X.columns
            ):
                logger.error(
                    f"❌ Incompatibilidade: modelo espera {model.n_features_in_} features, "
                    f"mas o serviço enviou {len(X.columns)}."
                )
                return None

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
