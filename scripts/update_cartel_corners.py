"""
Script rapido para atualizar apenas o campo 'corner' nos cartéis dos lutadores.
Não reimporta dados — só reprocessa os cartéis existentes adicionando o corner.
"""

import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.settings import Settings
from app.database.models.base import Event, Fight, Fighter

settings = Settings()


def main():
    db_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        fighters = session.query(Fighter).filter(Fighter.ufcstats_id.isnot(None)).all()
        total = len(fighters)
        print(f"\nAtualizando cartel de {total} lutadores para adicionar 'corner'...")
        start = time.time()
        updated = 0
        skipped = 0

        for i, fighter in enumerate(fighters, 1):
            try:
                fights = (
                    session.query(Fight, Event)
                    .join(Event, Fight.event_id == Event.id)
                    .filter(
                        (Fight.fighter1_id == fighter.id) | (Fight.fighter2_id == fighter.id),
                        Fight.status == "completed",
                    )
                    .order_by(Event.date.desc())
                    .all()
                )

                if not fights:
                    skipped += 1
                    continue

                cartel = []
                for fight, event in fights:
                    is_fighter1 = fight.fighter1_id == fighter.id
                    opponent_id = fight.fighter2_id if is_fighter1 else fight.fighter1_id
                    opponent = session.get(Fighter, opponent_id)

                    result = "N/A"
                    if fight.result_type == "Draw":
                        result = "D"
                    elif fight.winner_id:
                        result = "W" if fight.winner_id == fighter.id else "L"

                    cartel_entry = {
                        "opponent": opponent.name if opponent else "Unknown",
                        "result": result,
                        "method": fight.result_type or "Unknown",
                        "round": fight.finish_round,
                        "date": event.date.strftime("%d/%m/%Y") if event.date else None,
                        "organization": "UFC",
                        "corner": "Red" if is_fighter1 else "Blue",
                    }
                    cartel.append(cartel_entry)

                fighter.cartel = cartel
                updated += 1

                if i % 200 == 0:
                    session.commit()
                    elapsed = time.time() - start
                    print(f"  Progresso: {i}/{total} — {elapsed:.0f}s | {updated} atualizados, {skipped} sem lutas")

            except Exception as e:
                print(f"  Erro ao atualizar {fighter.name}: {e}")
                continue

        session.commit()
        elapsed = time.time() - start
        print(f"\nConcluido em {int(elapsed//60)}m{int(elapsed%60):02d}s")
        print(f"   {updated} cartéis atualizados com 'corner'")
        if skipped:
            print(f"   {skipped} lutadores sem lutas completadas (pulados)")

    except Exception as e:
        print(f"\nErro critico: {e}")
        session.rollback()
        raise

    finally:
        session.close()


if __name__ == "__main__":
    main()
