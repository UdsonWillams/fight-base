"""ML Model Loader - Carrega modelo de predição do GCS ou Local"""

import asyncio
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
    _lock = asyncio.Lock()
    _gcs_model_path = "gs://modelo-mma-fightbase/mma_model_v1.joblib"

    _default_local_paths = [
        "models/mma_model_v1.joblib",
        "models/mma_model.joblib",
    ]

    @classmethod
    async def load_model(cls, force_reload: bool = False):
        """Carrega o modelo do GCS ou Local (cached, thread-safe)"""
        async with cls._lock:
            if cls._model is not None and not force_reload:
                return cls._model

            local_path = os.getenv("LOCAL_MODEL_PATH")
            if local_path and os.path.exists(local_path):
                try:
                    logger.info(f"🤖 Carregando modelo ML Local de {local_path}")
                    cls._model = joblib.load(local_path)
                    cls._log_model_info_success("Local (env)")
                    return cls._model
                except Exception as e:
                    logger.error(f"❌ Erro ao carregar modelo local: {e}")

            if not local_path:
                for default_path in cls._default_local_paths:
                    if os.path.exists(default_path):
                        try:
                            logger.info(f"🤖 Modelo local detectado: {default_path}")
                            cls._model = joblib.load(default_path)
                            cls._log_model_info_success("Local (auto)")
                            return cls._model
                        except Exception as e:
                            logger.error(f"❌ Erro ao carregar modelo local: {e}")

            try:
                if gcsfs is None:
                    logger.warning(
                        "⚠️  Biblioteca gcsfs não instalada. Pule para uso local."
                    )
                    raise ImportError("gcsfs not installed")

                logger.info(
                    f"🤖 Tentando carregar modelo ML do GCS: {cls._gcs_model_path}"
                )

                credentials_path = os.getenv(
                    "GCP_CREDENTIALS_PATH", "service_account.json"
                )

                if os.path.exists(credentials_path):
                    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
                    logger.info(f"🔐 Usando credenciais: {credentials_path}")
                else:
                    logger.warning(
                        f"⚠️  Credenciais GCS não encontradas: {credentials_path}"
                    )

                fs = gcsfs.GCSFileSystem(
                    token=credentials_path if os.path.exists(credentials_path) else None
                )

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
    async def get_model(cls):
        """Retorna o modelo carregado"""
        if cls._model is None:
            cls._model = await cls.load_model()
        return cls._model


# Singleton instance
ml_model_loader = MLModelLoader()
