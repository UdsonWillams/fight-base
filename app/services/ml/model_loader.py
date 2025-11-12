"""ML Model Loader - Carrega modelo de predição do GCS"""

import os

import gcsfs
import joblib

from app.core.logger import logger


class MLModelLoader:
    """Carregador do modelo de ML"""

    _model = None
    _model_path = "gs://modelo-mma-fightbase/mma_model_v1.joblib"

    @classmethod
    def load_model(cls, force_reload=False):
        """Carrega o modelo do GCS (cached)"""
        if cls._model is not None and not force_reload:
            return cls._model

        try:
            logger.info(f"🤖 Carregando modelo ML de {cls._model_path}")

            # Autenticação GCS
            credentials_path = os.getenv("GCP_CREDENTIALS_PATH", "service_account.json")

            if os.path.exists(credentials_path):
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
                logger.info(f"🔐 Usando credenciais: {credentials_path}")
            else:
                logger.warning(f"⚠️  Credenciais não encontradas: {credentials_path}")

            # Conectar ao GCS
            fs = gcsfs.GCSFileSystem(
                token=credentials_path if os.path.exists(credentials_path) else None
            )

            # Carregar modelo
            with fs.open(cls._model_path, "rb") as f:
                cls._model = joblib.load(f)

            logger.info("✅ Modelo ML carregado com sucesso!")
            logger.info(f"   Tipo: {type(cls._model).__name__}")
            logger.info(f"   Features: {cls._model.n_features_in_}")
            return cls._model

        except Exception as e:
            logger.error(f"❌ Erro ao carregar modelo ML: {e}")
            logger.warning("⚠️  Sistema funcionará sem predições ML")
            return None

    @classmethod
    def get_model(cls):
        """Retorna o modelo carregado"""
        if cls._model is None:
            cls._model = cls.load_model()
        return cls._model


# Singleton instance
ml_model_loader = MLModelLoader()
