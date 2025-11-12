"""
Script para exportar dados importantes antes de resetar migrations
"""

import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.settings import Settings
from app.database.models.base import Fighter, Event, Fight, FightSimulation, User

settings = Settings()
engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
Session = sessionmaker(bind=engine)


def export_data():
    """Exporta dados importantes do banco"""
    
    session = Session()
    
    print("📦 EXPORTANDO DADOS DO BANCO\n")
    print("=" * 60)
    
    backup_data = {
        "users": [],
        "fighters": [],
        "events": [],
        "fights": [],
        "fight_simulations": []
    }
    
    try:
        # Exportar usuários
        users = session.query(User).all()
        for user in users:
            backup_data["users"].append({
                "id": str(user.id),
                "email": user.email,
                "name": user.name,
                "role": user.role,
                "is_active": user.is_active
            })
        print(f"✓ {len(users)} usuários exportados")
        
        # Exportar lutadores
        fighters = session.query(Fighter).all()
        for fighter in fighters:
            backup_data["fighters"].append({
                "id": str(fighter.id),
                "ufcstats_id": fighter.ufcstats_id,
                "name": fighter.name,
                "nickname": fighter.nickname,
                "wins": fighter.wins,
                "losses": fighter.losses,
                "draws": fighter.draws,
                "is_real": fighter.is_real,
                "creator_id": str(fighter.creator_id)
            })
        print(f"✓ {len(fighters)} lutadores exportados")
        
        # Exportar eventos
        events = session.query(Event).all()
        for event in events:
            backup_data["events"].append({
                "id": str(event.id),
                "ufcstats_id": event.ufcstats_id,
                "name": event.name,
                "date": event.date.isoformat() if event.date else None,
                "location": event.location,
                "organization": event.organization,
                "status": event.status,
                "creator_id": str(event.creator_id)
            })
        print(f"✓ {len(events)} eventos exportados")
        
        # Exportar lutas
        fights = session.query(Fight).all()
        for fight in fights:
            backup_data["fights"].append({
                "id": str(fight.id),
                "ufcstats_id": fight.ufcstats_id,
                "event_id": str(fight.event_id),
                "fighter1_id": str(fight.fighter1_id),
                "fighter2_id": str(fight.fighter2_id),
                "winner_id": str(fight.winner_id) if fight.winner_id else None,
                "result_type": fight.result_type,
                "status": fight.status
            })
        print(f"✓ {len(fights)} lutas exportadas")
        
        # Exportar simulações
        simulations = session.query(FightSimulation).all()
        for sim in simulations:
            backup_data["fight_simulations"].append({
                "id": str(sim.id),
                "fighter1_id": str(sim.fighter1_id),
                "fighter2_id": str(sim.fighter2_id),
                "winner_id": str(sim.winner_id),
                "result_type": sim.result_type
            })
        print(f"✓ {len(simulations)} simulações exportadas")
        
        # Salvar em arquivo
        backup_file = "backup_data.json"
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2, ensure_ascii=False)
        
        print("\n" + "=" * 60)
        print(f"✅ Backup salvo em: {backup_file}")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Erro ao exportar dados: {str(e)}")
        return False
    
    finally:
        session.close()
    
    return True


if __name__ == "__main__":
    success = export_data()
    sys.exit(0 if success else 1)
