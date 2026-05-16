"""Atualiza categorias de peso (actual_weight_class) dos lutadores no banco
usando o datasets/UFC.csv, com busca case-insensitive por nome."""

import csv
import sys
from datetime import datetime

sys.path.append('.')

from app.core.settings import Settings
from app.database.models.base import Fighter
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

settings = Settings()
db_url = settings.DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://')
engine = create_engine(db_url)
Session = sessionmaker(bind=engine)


def parse_date(date_str: str):
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y", "%B %d, %Y"):
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except Exception:
            continue
    return None


def main():
    session = Session()
    try:
        # 1) Ler CSV e mapear última categoria de peso por nome (case-insensitive)
        fighter_weight_classes = {}
        csv_path = "datasets/UFC.csv"

        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                date_str = row.get("date", "").strip()
                fight_date = parse_date(date_str)
                if not fight_date:
                    continue

                division = row.get("division", "").strip()
                if not division:
                    continue

                for key in ("r_name", "b_name"):
                    name = row.get(key, "").strip()
                    if not name:
                        continue
                    name_lower = name.lower()
                    if (
                        name_lower not in fighter_weight_classes
                        or fight_date > fighter_weight_classes[name_lower][1]
                    ):
                        fighter_weight_classes[name_lower] = (division, fight_date)

        print(f"Lutadores mapeados no CSV: {len(fighter_weight_classes)}")

        # 2) Buscar todos os lutadores do banco
        fighters = session.query(Fighter).filter(Fighter.deleted_at.is_(None)).all()
        print(f"Lutadores no banco: {len(fighters)}")

        updated = 0
        not_found = 0

        for fighter in fighters:
            name_lower = fighter.name.lower()
            # Tentar match exato case-insensitive
            if name_lower in fighter_weight_classes:
                division, _ = fighter_weight_classes[name_lower]
                fighter.actual_weight_class = division
                updated += 1
            else:
                # Tentar match parcial: nome do CSV contido no nome do DB ou vice-versa
                matched = False
                for csv_name, (division, _) in fighter_weight_classes.items():
                    if csv_name in name_lower or name_lower in csv_name:
                        fighter.actual_weight_class = division
                        updated += 1
                        matched = True
                        break
                if not matched:
                    not_found += 1

        session.commit()
        print(f"Atualizados: {updated}")
        print(f"Nao encontrados: {not_found}")

    except Exception as e:
        session.rollback()
        print(f"Erro: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
