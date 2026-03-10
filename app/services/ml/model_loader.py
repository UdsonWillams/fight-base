"""ML Model Loader - Carrega modelo de predição do GCS ou Local"""

import os
import joblib

try:
    import gcsfs
except ImportError:
    gcsfs = None

from app.core.logger import logger


class MLModelLoader:
    """Carregador do modelo de ML"""

    _model = None
    _gcs_model_path = "gs://modelo-mma-fightbase/mma_model_v1.joblib"

    @classmethod
    def load_model(cls, force_reload=False):
        """Carrega o modelo do GCS ou Local (cached)"""
        if cls._model is not None and not force_reload:
            return cls._model

        # 1. Tentar carregar localmente se configurado
        local_path = os.getenv("LOCAL_MODEL_PATH")
        if local_path and os.path.exists(local_path):
            try:
                logger.info(f"🤖 Carregando modelo ML Local de {local_path}")
                cls._model = joblib.load(local_path)
                cls._log_model_info_success("Local")
                return cls._model
            except Exception as e:
                logger.error(f"❌ Erro ao carregar modelo local: {e}")

        # 2. Tentar carregar do GCS
        try:
            if gcsfs is None:
                logger.warning(
                    "⚠️  Biblioteca gcsfs não instalada. Pule para uso local."
                )
                raise ImportError("gcsfs not installed")

            logger.info(f"🤖 Tentando carregar modelo ML do GCS: {cls._gcs_model_path}")

            # Autenticação GCS
            credentials_path = os.getenv("GCP_CREDENTIALS_PATH", "service_account.json")

            if os.path.exists(credentials_path):
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
                logger.info(f"🔐 Usando credenciais: {credentials_path}")
            else:
                logger.warning(
                    f"⚠️  Credenciais GCS não encontradas: {credentials_path}"
                )
                # Sem credenciais, gcsfs pode falhar se o bucket não for público

            # Conectar ao GCS
            fs = gcsfs.GCSFileSystem(
                token=credentials_path if os.path.exists(credentials_path) else None
            )

            # Carregar modelo
            with fs.open(cls._gcs_model_path, "rb") as f:
                cls._model = joblib.load(f)

            cls._log_model_info_success("GCS")
            return cls._model

        except Exception as e:
            logger.error(f"❌ Erro ao carregar modelo ML (GCS/Local): {e}")
            logger.warning("⚠️  Sistema funcionará sem predições ML (Dummy Mode)")
            return None

    @classmethod
    def _log_model_info_success(cls, source):
        logger.info(f"✅ Modelo ML carregado com sucesso via {source}!")
        logger.info(f"   Tipo: {type(cls._model).__name__}")
        if hasattr(cls._model, "n_features_in_"):
            logger.info(f"   Features: {cls._model.n_features_in_}")

    @classmethod
    def get_model(cls):
        """Retorna o modelo carregado"""
        if cls._model is None:
            cls._model = cls.load_model()
        return cls._model


# Singleton instance
ml_model_loader = MLModelLoader()
