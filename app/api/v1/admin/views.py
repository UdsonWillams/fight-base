"""
Admin endpoints para operações administrativas como importação de dados e treinamento de modelo
"""

import csv
import subprocess
import sys
from datetime import datetime
from typing import Any, Dict
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.api.v1.auth.dependencies import require_admin
from app.core.logger import logger
from app.core.settings import get_settings
from app.database.models.base import Fighter, User

router = APIRouter()

# Criar engine sync para operações de importação
settings = get_settings()
sync_engine = create_engine(settings.DATABASE_URL_SYNC)
SyncSessionLocal = sessionmaker(bind=sync_engine)

# Dicionário para rastrear status das importações em andamento
import_tasks_status: Dict[str, Dict[str, Any]] = {}


def get_sync_session() -> Session:
    """Helper para criar session síncrona para importações"""
    session = SyncSessionLocal()
    try:
        return session
    finally:
        pass  # Session será fechada manualmente após uso


def run_ufc_import(task_id: str, user_id: str):
    """
    Função que roda a importação em background
    """
    session = get_sync_session()
    try:
        import_tasks_status[task_id] = {
            "status": "running",
            "message": "Importação iniciada",
            "progress": 0,
        }

        from scripts.import_ufc_dataset import UFCDatasetImporter

        # Buscar usuário
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            import_tasks_status[task_id] = {
                "status": "error",
                "message": "Usuário não encontrado",
            }
            return

        importer = UFCDatasetImporter(session)

        # 1. Importar lutadores
        logger.info(f"[{task_id}] Importando lutadores...")
        import_tasks_status[task_id]["progress"] = 10
        import_tasks_status[task_id]["message"] = "Importando lutadores..."
        importer.import_fighters("datasets/fighter_details.csv", user)

        # 2. Importar eventos
        logger.info(f"[{task_id}] Importando eventos...")
        import_tasks_status[task_id]["progress"] = 30
        import_tasks_status[task_id]["message"] = "Importando eventos..."
        importer.import_events("datasets/event_details.csv", user)

        # 3. Importar lutas
        logger.info(f"[{task_id}] Importando lutas...")
        import_tasks_status[task_id]["progress"] = 50
        import_tasks_status[task_id]["message"] = "Importando lutas..."
        importer.import_fights("datasets/fight_details.csv")

        # 4. Popular vencedores
        logger.info(f"[{task_id}] Populando vencedores...")
        import_tasks_status[task_id]["progress"] = 55
        import_tasks_status[task_id]["message"] = "Populando vencedores..."
        importer.populate_fight_winners("datasets/UFC.csv")

        # 5. Agregar ML stats (SLpM, TD avg, KO/sub wins)
        logger.info(f"[{task_id}] Agregando ML stats...")
        import_tasks_status[task_id]["progress"] = 65
        import_tasks_status[task_id]["message"] = "Agregando estatisticas ML..."
        importer.update_fighter_ml_stats()

        # 6. Atualizar nomes dos eventos
        logger.info(f"[{task_id}] Atualizando nomes dos eventos...")
        import_tasks_status[task_id]["progress"] = 75
        import_tasks_status[task_id]["message"] = "Atualizando nomes dos eventos..."
        importer.update_event_names()

        # 7. Atualizar cartel dos lutadores
        logger.info(f"[{task_id}] Atualizando cartel dos lutadores...")
        import_tasks_status[task_id]["progress"] = 85
        import_tasks_status[task_id]["message"] = "Atualizando cartel dos lutadores..."
        importer.update_fighter_cartels()

        # 8. Atualizar categorias de peso
        logger.info(f"[{task_id}] Atualizando categorias de peso...")
        import_tasks_status[task_id]["progress"] = 92
        import_tasks_status[task_id]["message"] = "Atualizando categorias de peso..."
        importer.update_weight_classes()

        # 9. Recalcular atributos de jogo (ML stats + win rate)
        logger.info(f"[{task_id}] Recalculando atributos...")
        import_tasks_status[task_id]["progress"] = 98
        import_tasks_status[task_id]["message"] = (
            "Recalculando atributos dos lutadores..."
        )
        importer.recalculate_fighter_attributes()

        # Concluído
        import_tasks_status[task_id] = {
            "status": "completed",
            "message": "Importação concluída com sucesso",
            "progress": 100,
            "stats": importer.stats,
        }
        logger.info(f"[{task_id}] Importação concluída!")

    except Exception as e:
        logger.error(f"[{task_id}] Erro na importação: {str(e)}")
        import_tasks_status[task_id] = {
            "status": "error",
            "message": f"Erro ao importar dataset: {str(e)}",
            "progress": 0,
        }
    finally:
        session.close()


@router.post("/import/ufc-dataset", status_code=status.HTTP_202_ACCEPTED)
async def import_ufc_dataset(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_admin),
) -> Dict[str, Any]:
    """
    Inicia importação do dataset completo do UFC em background
    Requer autenticação de admin

    Retorna um task_id que pode ser usado para verificar o status da importação
    """
    task_id = str(uuid4())

    # Adicionar tarefa ao background
    background_tasks.add_task(run_ufc_import, task_id, str(current_user.id))

    return {
        "status": "accepted",
        "message": "Importação iniciada em background",
        "task_id": task_id,
        "check_status_url": f"/api/v1/admin/import/status/{task_id}",
    }


@router.get("/import/status/{task_id}", status_code=status.HTTP_200_OK)
async def get_import_status(
    task_id: str,
    current_user: User = Depends(require_admin),
) -> Dict[str, Any]:
    """
    Verifica o status de uma importação em andamento
    """
    if task_id not in import_tasks_status:
        return {
            "status": "not_found",
            "message": "Task não encontrada",
        }

    return import_tasks_status[task_id]


@router.post("/import/update-weight-classes", status_code=status.HTTP_200_OK)
async def update_weight_classes(
    current_user: User = Depends(require_admin),
) -> Dict[str, Any]:
    """
    Atualiza apenas as categorias de peso dos lutadores
    Requer autenticação de admin
    """
    session = get_sync_session()
    try:
        # Ler UFC.csv e mapear categoria de peso da última luta de cada lutador
        fighter_weight_classes = {}

        with open("datasets/UFC.csv", "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row in reader:
                date_str = row.get("date", "").strip()
                if not date_str:
                    continue

                # Parse data - tentar múltiplos formatos
                fight_date = None
                for date_format in ["%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y"]:
                    try:
                        fight_date = datetime.strptime(date_str, date_format)
                        break
                    except Exception:
                        continue  # nosec

                if not fight_date:
                    continue

                division = row.get("division", "").strip()
                if not division:
                    continue

                r_fighter = row.get("r_name", "").strip()
                b_fighter = row.get("b_name", "").strip()

                # Atualiza categoria de peso se essa luta for mais recente
                for fighter_name in [r_fighter, b_fighter]:
                    if fighter_name:
                        if (
                            fighter_name not in fighter_weight_classes
                            or fight_date > fighter_weight_classes[fighter_name][1]
                        ):
                            fighter_weight_classes[fighter_name] = (
                                division,
                                fight_date,
                            )

        # Atualizar no banco
        updated = 0
        not_found = 0

        for fighter_name, (weight_class, _) in fighter_weight_classes.items():
            fighter = (
                session.query(Fighter).filter(Fighter.name == fighter_name).first()
            )
            if fighter:
                fighter.actual_weight_class = weight_class
                updated += 1
            else:
                not_found += 1

        session.commit()

        return {
            "status": "success",
            "message": "Categorias de peso atualizadas",
            "updated": updated,
            "not_found": not_found,
            "total_in_csv": len(fighter_weight_classes),
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Erro ao atualizar categorias: {str(e)}",
        }
    finally:
        session.close()


# Dicionario para rastrear status de treinamento em andamento
train_tasks_status: Dict[str, Dict[str, Any]] = {}


def run_model_training(task_id: str, quick: bool = False):
    """Executa o script de treinamento V2 em background"""
    try:
        train_tasks_status[task_id] = {
            "status": "running",
            "message": "Treinamento iniciado",
            "progress": 5,
        }

        script_path = "scripts/train_model_v2_db.py"
        cmd = [sys.executable, script_path]
        if quick:
            cmd.append("--quick")
            train_tasks_status[task_id]["message"] = (
                "Treinando modelo V2 (modo rapido)..."
            )

        logger.info(f"[{task_id}] Executando: {' '.join(cmd)}")
        train_tasks_status[task_id]["progress"] = 15
        train_tasks_status[task_id]["message"] = (
            "Extraindo features e treinando ensemble..."
        )

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)

        if result.returncode == 0:
            train_tasks_status[task_id] = {
                "status": "completed",
                "message": "Modelo treinado com sucesso! Salvo em models/mma_model_v2.joblib",
                "progress": 100,
                "output": result.stdout[-3000:],
            }
            logger.info(f"[{task_id}] Treinamento concluido!")

            try:
                import asyncio
                from app.services.ml.model_loader import ml_model_loader

                async def reload():
                    await ml_model_loader.load_model(force_reload=True)

                asyncio.run(reload())
                train_tasks_status[task_id]["message"] += (
                    " | Modelo recarregado no servidor."
                )
            except Exception as e:
                logger.warning(
                    f"[{task_id}] Modelo treinado mas falha ao recarregar: {e}"
                )
                train_tasks_status[task_id]["message"] += (
                    " | ATENCAO: Reinicie o servidor para usar o novo modelo."
                )
        else:
            train_tasks_status[task_id] = {
                "status": "error",
                "message": f"Erro no treinamento. Codigo de saida: {result.returncode}",
                "output": result.stderr[-3000:] or result.stdout[-3000:],
                "progress": 0,
            }
            logger.error(f"[{task_id}] Erro no treinamento: {result.stderr[-500:]}")

    except subprocess.TimeoutExpired:
        train_tasks_status[task_id] = {
            "status": "error",
            "message": "Timeout: treinamento excedeu 60 minutos",
            "progress": 0,
        }
    except Exception as e:
        logger.error(f"[{task_id}] Erro no treinamento: {str(e)}")
        train_tasks_status[task_id] = {
            "status": "error",
            "message": f"Erro ao treinar modelo: {str(e)}",
            "progress": 0,
        }


@router.post("/train-model", status_code=status.HTTP_202_ACCEPTED)
async def train_model(
    background_tasks: BackgroundTasks,
    quick: bool = False,
    current_user: User = Depends(require_admin),
):
    """
    Inicia treinamento do modelo ML V2 (Stacking Ensemble) em background.

    - **quick**: Se true, usa 5 iteracoes e 3-fold CV (rapido).
      Se false, 20 iteracoes e 5-fold CV (completo, ~15-30min).

    Retorna um task_id para verificar o status.
    """
    task_id = str(uuid4())

    background_tasks.add_task(run_model_training, task_id, quick)

    return {
        "task_id": task_id,
        "status": "accepted",
        "message": "Treinamento iniciado em background",
        "check_status_url": f"/api/v1/admin/train-model/status/{task_id}",
    }


@router.get("/train-model/status/{task_id}", status_code=status.HTTP_200_OK)
async def get_train_status(
    task_id: str,
    current_user: User = Depends(require_admin),
):
    """Verifica o status de um treinamento em andamento"""
    if task_id not in train_tasks_status:
        return {
            "status": "error",
            "message": "Task nao encontrada. Pode ter expirado ou nunca ter existido.",
        }

    return train_tasks_status[task_id]
