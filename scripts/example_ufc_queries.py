"""
Exemplo de uso dos dados importados do UFC Dataset
"""

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

from app.core.settings import Settings
from app.database.models.base import Fighter, Event, Fight

settings = Settings()
engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
Session = sessionmaker(bind=engine)


def example_queries():
    """Exemplos de consultas úteis após importação"""
    
    session = Session()
    
    print("🥊 EXEMPLOS DE CONSULTAS - DATASET UFC\n")
    print("=" * 60)
    
    # 1. Lutadores com mais vitórias
    print("\n📊 TOP 10 - Mais Vitórias")
    print("-" * 60)
    top_winners = session.query(Fighter).filter(
        Fighter.ufcstats_id.isnot(None)
    ).order_by(Fighter.wins.desc()).limit(10).all()
    
    for i, fighter in enumerate(top_winners, 1):
        record = f"{fighter.wins}-{fighter.losses}-{fighter.draws}"
        print(f"{i:2}. {fighter.name:30} | {record:10} | {fighter.stance or 'N/A':10}")
    
    # 2. Lutadores com melhor defesa de striking
    print("\n🛡️  TOP 10 - Melhor Defesa de Striking")
    print("-" * 60)
    top_defense = session.query(Fighter).filter(
        Fighter.str_def.isnot(None),
        Fighter.ufcstats_id.isnot(None)
    ).order_by(Fighter.str_def.desc()).limit(10).all()
    
    for i, fighter in enumerate(top_defense, 1):
        print(f"{i:2}. {fighter.name:30} | Str Def: {fighter.str_def:5.1f}% | TD Def: {fighter.td_def or 0:5.1f}%")
    
    # 3. Eventos com mais lutas
    print("\n🎪 TOP 10 - Eventos com Mais Lutas")
    print("-" * 60)
    top_events = session.query(
        Event.name,
        Event.date,
        Event.location,
        func.count(Fight.id).label('fight_count')
    ).join(Fight).filter(
        Event.ufcstats_id.isnot(None)
    ).group_by(Event.id).order_by(func.count(Fight.id).desc()).limit(10).all()
    
    for i, (name, date, location, count) in enumerate(top_events, 1):
        date_str = date.strftime("%Y-%m-%d") if date else "N/A"
        print(f"{i:2}. {name[:40]:40} | {date_str} | {count} lutas")
    
    # 4. Lutas com mais knockdowns combinados
    print("\n💥 TOP 10 - Lutas com Mais Knockdowns")
    print("-" * 60)
    top_kd_fights = session.query(Fight).filter(
        Fight.r_kd.isnot(None),
        Fight.b_kd.isnot(None),
        Fight.ufcstats_id.isnot(None)
    ).order_by((Fight.r_kd + Fight.b_kd).desc()).limit(10).all()
    
    for i, fight in enumerate(top_kd_fights, 1):
        fighter1 = session.query(Fighter).get(fight.fighter1_id)
        fighter2 = session.query(Fighter).get(fight.fighter2_id)
        total_kd = (fight.r_kd or 0) + (fight.b_kd or 0)
        print(f"{i:2}. {fighter1.name:20} vs {fighter2.name:20} | KDs: {total_kd}")
    
    # 5. Estatísticas gerais
    print("\n📈 ESTATÍSTICAS GERAIS")
    print("-" * 60)
    
    total_fighters = session.query(func.count(Fighter.id)).filter(
        Fighter.ufcstats_id.isnot(None)
    ).scalar()
    
    total_events = session.query(func.count(Event.id)).filter(
        Event.ufcstats_id.isnot(None)
    ).scalar()
    
    total_fights = session.query(func.count(Fight.id)).filter(
        Fight.ufcstats_id.isnot(None)
    ).scalar()
    
    avg_slpm = session.query(func.avg(Fighter.slpm)).filter(
        Fighter.slpm.isnot(None)
    ).scalar()
    
    avg_str_acc = session.query(func.avg(Fighter.str_acc)).filter(
        Fighter.str_acc.isnot(None)
    ).scalar()
    
    print(f"Total de Lutadores: {total_fighters}")
    print(f"Total de Eventos:   {total_events}")
    print(f"Total de Lutas:     {total_fights}")
    print(f"Média SLPM:         {avg_slpm:.2f}")
    print(f"Média Str Acc:      {avg_str_acc:.1f}%")
    
    # 6. Exemplo de cartel de um lutador
    print("\n🏆 EXEMPLO DE CARTEL")
    print("-" * 60)
    
    # Buscar um lutador famoso
    famous_fighter = session.query(Fighter).filter(
        Fighter.name.ilike('%conor%mcgregor%')
    ).first()
    
    if famous_fighter:
        print(f"\nLutador: {famous_fighter.name}")
        print(f"Record: {famous_fighter.wins}-{famous_fighter.losses}-{famous_fighter.draws}")
        print(f"Stance: {famous_fighter.stance or 'N/A'}")
        print(f"Height: {famous_fighter.height_cm:.0f}cm" if famous_fighter.height_cm else "Height: N/A")
        print(f"Reach: {famous_fighter.reach_cm:.0f}cm" if famous_fighter.reach_cm else "Reach: N/A")
        print("\nÚltimas 5 lutas:")
        
        if famous_fighter.cartel:
            for i, fight in enumerate(famous_fighter.cartel[:5], 1):
                result_emoji = "✅" if fight['result'] == 'W' else "❌" if fight['result'] == 'L' else "🤝"
                print(f"  {i}. {result_emoji} vs {fight['opponent']} - {fight['method']} (R{fight.get('round', '?')})")
    
    print("\n" + "=" * 60)
    session.close()


if __name__ == "__main__":
    example_queries()
