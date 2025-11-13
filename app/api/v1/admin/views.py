"""
Admin endpoints para operações administrativas como importação de dados
"""

import csv
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends, status
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.api.v1.auth.dependencies import require_admin
from app.core.settings import get_settings
from app.database.models.schemas import Fighter, User

router = APIRouter()

# Criar engine sync para operações de importação
settings = get_settings()
sync_engine = create_engine(settings.DATABASE_URL_SYNC)
SyncSessionLocal = sessionmaker(bind=sync_engine)


def get_sync_session() -> Session:
    """Helper para criar session síncrona para importações"""
    session = SyncSessionLocal()
    try:
        return session
    finally:
        pass  # Session será fechada manualmente após uso


@router.post("/import/ufc-dataset", status_code=status.HTTP_200_OK)
async def import_ufc_dataset(
    current_user: User = Depends(require_admin),
) -> Dict[str, Any]:
    """
    Importa dataset completo do UFC (fighters, events, fights)
    Requer autenticação de admin
    """
    session = get_sync_session()
    try:
        from scripts.import_ufc_dataset import UFCDatasetImporter

        importer = UFCDatasetImporter(session)

        # 1. Importar lutadores
        importer.import_fighters("datasets/fighter_details.csv", current_user)

        # 2. Importar eventos
        importer.import_events("datasets/event_details.csv", current_user)

        # 3. Importar lutas
        importer.import_fights("datasets/fight_details.csv")

        # 4. Popular vencedores
        importer.populate_fight_winners("datasets/UFC.csv")

        # 5. Atualizar nomes dos eventos
        importer.update_event_names()

        # 6. Atualizar cartel dos lutadores
        importer.update_fighter_cartels()

        # 7. Atualizar categorias de peso
        importer.update_weight_classes()

        return {
            "status": "success",
            "message": "Dataset UFC importado com sucesso",
            "stats": importer.stats,
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Erro ao importar dataset: {str(e)}",
        }
    finally:
        session.close()


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
                        continue

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
