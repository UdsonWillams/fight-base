"""
Admin endpoints para operações administrativas como importação de dados e treinamento de modelo
"""

import csv
import subprocess
import sys
import threading
from datetime import datetime, timezone
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


def _cleanup_old_tasks(status_dict: Dict[str, Dict[str, Any]], max_age_hours: int = 24):
    """Remove tasks concluídas/erro/timeout com mais de max_age_hours."""
    now = datetime.now(timezone.utc)
    to_remove = []
    for tid, info in list(status_dict.items()):
        if info.get("status") in ("completed", "error", "timeout", "cancelled"):
            created = info.get("created_at")
            if created:
                age = (now - created).total_seconds() / 3600
                if age > max_age_hours:
                    to_remove.append(tid)
    for tid in to_remove:
        del status_dict[tid]
    if to_remove:
        logger.info(f"Cleaned up {len(to_remove)} old task entries")


def run_ufc_import(task_id: str, user_id: str):
    """
    Função que roda a importação em background com timeout de 3 horas.
    Suporta cancelamento via POST /admin/import/cancel/{task_id}.
    """
    _cleanup_old_tasks(import_tasks_status)

    import_tasks_status[task_id] = {
        "status": "running",
        "message": "Importação iniciada",
        "progress": 0,
        "created_at": datetime.now(timezone.utc),
    }

    timeout_seconds = get_settings().IMPORT_TIMEOUT_SECONDS
    result_container = {"error": None, "completed": False}
    importer_ref = {"importer": None}

    def _do_import():
        session = get_sync_session()
        try:
            from scripts.import_ufc_dataset import UFCDatasetImporter

            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                import_tasks_status[task_id] = {
                    "status": "error",
                    "message": "Usuário não encontrado",
                    "created_at": import_tasks_status[task_id].get("created_at"),
                }
                return

            importer = UFCDatasetImporter(session)
            importer_ref["importer"] = importer
            import_tasks_status[task_id]["_importer"] = importer

            for step_num, (step_fn, step_args, step_label, progress_pct) in enumerate(
                [
                    (
                        importer.import_fighters,
                        ("datasets/fighter_details.csv", user),
                        "Importando lutadores",
                        10,
                    ),
                    (
                        importer.import_events,
                        ("datasets/event_details.csv", user),
                        "Importando eventos",
                        30,
                    ),
                    (
                        importer.import_fights,
                        ("datasets/fight_details.csv",),
                        "Importando lutas",
                        50,
                    ),
                    (
                        importer.populate_fight_winners,
                        ("datasets/UFC.csv",),
                        "Populando vencedores",
                        55,
                    ),
                    (
                        importer.update_fighter_ml_stats,
                        (),
                        "Agregando estatisticas ML",
                        65,
                    ),
                    (
                        importer.update_event_names,
                        (),
                        "Atualizando nomes dos eventos",
                        75,
                    ),
                    (
                        importer.update_fighter_cartels,
                        (),
                        "Atualizando cartel dos lutadores",
                        85,
                    ),
                    (
                        importer.update_weight_classes,
                        (),
                        "Atualizando categorias de peso",
                        92,
                    ),
                    (
                        importer.recalculate_fighter_attributes,
                        (),
                        "Recalculando atributos",
                        98,
                    ),
                ],
                1,
            ):
                if importer._cancelled.is_set():
                    import_tasks_status[task_id] = {
                        "status": "cancelled",
                        "message": "Importação cancelada pelo usuário",
                        "progress": import_tasks_status[task_id].get("progress", 0),
                        "created_at": import_tasks_status[task_id].get("created_at"),
                    }
                    logger.info(
                        f"[{task_id}] Importação cancelada após step {step_num}"
                    )
                    return

                logger.info(f"[{task_id}] Step {step_num}/9: {step_label}")
                import_tasks_status[task_id]["progress"] = progress_pct
                import_tasks_status[task_id]["message"] = step_label

                if step_args:
                    step_fn(*step_args)
                else:
                    step_fn()

            import_tasks_status[task_id] = {
                "status": "completed",
                "message": "Importação concluída com sucesso",
                "progress": 100,
                "stats": importer.stats,
                "created_at": import_tasks_status[task_id].get("created_at"),
            }
            logger.info(f"[{task_id}] Importação concluída!")
            result_container["completed"] = True

        except Exception as e:
            logger.error(f"[{task_id}] Erro na importação: {str(e)}")
            import_tasks_status[task_id] = {
                "status": "error",
                "message": f"Erro ao importar dataset: {str(e)}",
                "progress": 0,
                "created_at": import_tasks_status[task_id].get("created_at"),
            }
            result_container["error"] = str(e)
        finally:
            session.close()

    thread = threading.Thread(target=_do_import, daemon=True)
    thread.start()
    thread.join(timeout=timeout_seconds)

    if thread.is_alive():
        importer = importer_ref["importer"]
        if importer:
            importer.cancel()
        import_tasks_status[task_id] = {
            "status": "timeout",
            "message": f"Timeout: importação excedeu {timeout_seconds // 3600} horas",
            "progress": import_tasks_status[task_id].get("progress", 0),
            "created_at": import_tasks_status[task_id].get("created_at"),
        }
        logger.warning(
            f"[{task_id}] Importação cancelada por timeout ({timeout_seconds}s)"
        )


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
            "message": "Task não encontrada. Pode ter expirado ou nunca ter existido.",
        }

    return import_tasks_status[task_id]


@router.post("/import/cancel/{task_id}", status_code=status.HTTP_200_OK)
async def cancel_import(
    task_id: str,
    current_user: User = Depends(require_admin),
) -> Dict[str, Any]:
    """
    Cancela uma importação em andamento.
    A task será interrompida no próximo step da pipeline.
    """
    if task_id not in import_tasks_status:
        return {
            "status": "not_found",
            "message": "Task não encontrada.",
        }

    task_info = import_tasks_status[task_id]
    if task_info.get("status") != "running":
        return {
            "status": "error",
            "message": f"Task não está em execução (status atual: {task_info.get('status')})",
        }

    task_info["status"] = "cancelled"
    task_info["message"] = (
        "Cancelamento solicitado — aguardando step atual finalizar..."
    )
    logger.info(
        f"[{task_id}] Cancelamento solicitado pelo usuário {current_user.email}"
    )

    importer = task_info.pop("_importer", None)
    if importer is not None:
        importer.cancel()

    return {
        "status": "accepted",
        "message": "Solicitação de cancelamento registrada. A importação será interrompida no próximo step.",
        "task_id": task_id,
    }


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
    """Executa o script de treinamento V2 em background com progresso em tempo real."""
    import time

    train_tasks_status[task_id] = {
        "status": "running",
        "message": "Treinamento iniciado",
        "progress": 5,
        "created_at": datetime.now(timezone.utc),
        "output_lines": [],
    }

    script_path = "scripts/train_model_v2_db.py"
    cmd = [sys.executable, script_path]
    if quick:
        cmd.append("--quick")
        train_tasks_status[task_id]["message"] = "Treinando modelo V2 (modo rapido)..."
        expected_minutes = 10
    else:
        train_tasks_status[task_id]["message"] = (
            "Treinando modelo V2 (modo completo)..."
        )
        expected_minutes = 30

    logger.info(f"[{task_id}] Iniciando: {' '.join(cmd)}")

    # Mapa de marcadores de progresso (texto na stdout → progresso %)
    progress_markers = [
        ("Passo 1", 10),
        ("Passo 2", 20),
        ("Passo 3", 30),
        ("Passo 4", 40),
        ("Tuning RandomForest", 50),
        ("Tuning HistGradientBoosting", 65),
        ("Passo 5", 85),
        ("PIPELINE V2 CONCLUÍDO", 95),
    ]

    start_time = time.time()
    expected_seconds = expected_minutes * 60
    collected_output = []

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        def _read_output():
            for line in iter(process.stdout.readline, ""):
                if not line:
                    break
                collected_output.append(line)
                line_stripped = line.strip()
                if line_stripped:
                    train_tasks_status[task_id].setdefault("output_lines", []).append(
                        line_stripped
                    )
                    train_tasks_status[task_id]["output_lines"] = train_tasks_status[
                        task_id
                    ]["output_lines"][-200:]
                    for marker, pct in progress_markers:
                        if marker in line_stripped:
                            train_tasks_status[task_id]["progress"] = pct
                            train_tasks_status[task_id]["message"] = line_stripped[:120]
                            break

        import threading

        reader_thread = threading.Thread(target=_read_output, daemon=True)
        reader_thread.start()

        # Poll até o processo terminar ou timeout
        timeout_seconds = get_settings().MODEL_TRAIN_TIMEOUT_SECONDS
        poll_interval = 2.0
        last_progress = train_tasks_status[task_id]["progress"]

        while process.poll() is None:
            elapsed = time.time() - start_time
            if elapsed > timeout_seconds:
                process.kill()
                reader_thread.join(timeout=5)
                train_tasks_status[task_id] = {
                    "status": "error",
                    "message": f"Timeout: treinamento excedeu {timeout_seconds // 60} minutos",
                    "progress": train_tasks_status[task_id].get("progress", 0),
                    "created_at": train_tasks_status[task_id].get("created_at"),
                }
                logger.warning(f"[{task_id}] Treinamento cancelado por timeout")
                return

            # Progresso por tempo como fallback entre marcadores
            current_marker = train_tasks_status[task_id]["progress"]
            if current_marker == last_progress and current_marker < 95:
                time_based = min(
                    current_marker + 5,
                    int(elapsed / expected_seconds * 100),
                    95,
                )
                if time_based > current_marker:
                    train_tasks_status[task_id]["progress"] = time_based

            last_progress = train_tasks_status[task_id]["progress"]
            time.sleep(poll_interval)

        reader_thread.join(timeout=10)

        if process.returncode == 0:
            train_tasks_status[task_id] = {
                "status": "running",
                "message": "Modelo treinado! Recarregando no servidor...",
                "progress": 98,
                "created_at": train_tasks_status[task_id].get("created_at"),
                "output_lines": train_tasks_status[task_id].get("output_lines", []),
            }

            import asyncio
            from app.services.ml.model_loader import ml_model_loader

            async def reload():
                await ml_model_loader.load_model(force_reload=True)

            asyncio.run(reload())

            output_text = "".join(collected_output)
            train_tasks_status[task_id] = {
                "status": "completed",
                "message": "Modelo treinado com sucesso! Salvo em models/mma_model_v2.joblib | Modelo recarregado no servidor.",
                "progress": 100,
                "output": output_text[-3000:],
                "created_at": train_tasks_status[task_id].get("created_at"),
            }
            logger.info(
                f"[{task_id}] Treinamento concluido! "
                f"({(time.time() - start_time) / 60:.1f} min)"
            )
        else:
            output_text = "".join(collected_output)
            train_tasks_status[task_id] = {
                "status": "error",
                "message": f"Erro no treinamento. Codigo de saida: {process.returncode}",
                "output": output_text[-3000:],
                "progress": 0,
                "created_at": train_tasks_status[task_id].get("created_at"),
            }
            logger.error(
                f"[{task_id}] Erro no treinamento (exit={process.returncode}): "
                f"{output_text[-500:]}"
            )

    except Exception as e:
        logger.error(f"[{task_id}] Erro no treinamento: {str(e)}")
        train_tasks_status[task_id] = {
            "status": "error",
            "message": f"Erro ao treinar modelo: {str(e)}",
            "progress": 0,
            "created_at": train_tasks_status[task_id].get("created_at"),
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
