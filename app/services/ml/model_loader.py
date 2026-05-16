"""ML Model Loader - Carrega modelo de predição local"""

import asyncio
import os
import joblib

from app.core.logger import logger


class MLModelLoader:
    """Carregador do modelo de ML"""

    _model = None
    _lock = asyncio.Lock()

    _default_local_paths = [
        "models/mma_model_v2.joblib",
        "models/mma_model_v1.joblib",
        "models/mma_model.joblib",
    ]

    @classmethod
    async def load_model(cls, force_reload: bool = False):
        """Carrega o modelo local (cached, thread-safe)"""
        async with cls._lock:
            if cls._model is not None and not force_reload:
                return cls._model

            local_path = os.getenv("LOCAL_MODEL_PATH")
            if local_path and os.path.exists(local_path):
                try:
                    logger.info(f"🤖 Carregando modelo ML Local de {local_path}")
                    cls._model = joblib.load(local_path)
                    cls._log_model_info_success(local_path)
                    return cls._model
                except Exception as e:
                    logger.error(f"❌ Erro ao carregar modelo local: {e}")

            if not local_path:
                for default_path in cls._default_local_paths:
                    if os.path.exists(default_path):
                        try:
                            logger.info(f"🤖 Modelo local detectado: {default_path}")
                            cls._model = joblib.load(default_path)
                            cls._log_model_info_success(default_path)
                            return cls._model
                        except Exception as e:
                            logger.error(f"❌ Erro ao carregar modelo local: {e}")

            logger.warning(
                "⚠️  Modelo ML não encontrado. Sistema funcionará sem predições ML (Dummy Mode)"
            )
            return None

    @classmethod
    def _log_model_info_success(cls, source):
        logger.info(f"✅ Modelo ML carregado com sucesso de {source}!")
        logger.info(f"   Tipo: {type(cls._model).__name__}")
        if hasattr(cls._model, "n_features_in_"):
            logger.info(f"   Features: {cls._model.n_features_in_}")

    @classmethod
    async def get_model(cls):
        """Retorna o modelo carregado"""
        if cls._model is None:
            cls._model = await cls.load_model()
        return cls._model


# Singleton instance
ml_model_loader = MLModelLoader()
