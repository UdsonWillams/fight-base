#!/usr/bin/env python3
"""
Script de teste para validar a importação consolidada
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

from app.core.settings import Settings
from app.database.models.base import Event, Fight, Fighter

settings = Settings()


def test_import():
    """Testa se a importação consolidada funcionou"""
    print("\n🔍 VALIDANDO IMPORTAÇÃO CONSOLIDADA")
    print("=" * 60)

    engine = create_engine(settings.DATABASE_URL_SYNC)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # 1. Contar lutadores
        fighter_count = session.query(func.count(Fighter.id)).scalar()
        print(f"\n✅ Lutadores: {fighter_count}")

        # 2. Contar eventos
        event_count = session.query(func.count(Event.id)).scalar()
        print(f"✅ Eventos: {event_count}")

        # 3. Contar lutas
        fight_count = session.query(func.count(Fight.id)).scalar()
        print(f"✅ Lutas: {fight_count}")

        # 4. Verificar lutas com vencedor
        fights_with_winner = (
            session.query(func.count(Fight.id))
            .filter(Fight.winner_id.isnot(None))
            .scalar()
        )
        fights_without_winner = fight_count - fights_with_winner
        print(f"\n🏆 Lutas com vencedor: {fights_with_winner}")
        print(f"🤝 Lutas sem vencedor (empate/NC): {fights_without_winner}")

        # 5. Verificar cartel de um lutador específico
        tom = session.query(Fighter).filter_by(name="Tom Aspinall").first()
        if tom:
            print("\n👤 Teste com Tom Aspinall:")
            print(f"   • Cartel: {len(tom.cartel) if tom.cartel else 0} lutas")
            if tom.cartel and len(tom.cartel) > 0:
                first_fight = tom.cartel[0]
                print("   • Última luta:")
                print(f"     - Oponente: {first_fight.get('opponent')}")
                print(f"     - Resultado: {first_fight.get('result')}")
                print(f"     - Data: {first_fight.get('date')}")
                print(f"     - Método: {first_fight.get('method')}")

        # 6. Verificar Jessica Andrade (teste de gênero feminino)
        jessica = session.query(Fighter).filter_by(name="Jessica Andrade").first()
        if jessica:
            print("\n👤 Teste com Jessica Andrade:")
            print(f"   • Categoria: {jessica.actual_weight_class}")
            print(f"   • Cartel: {len(jessica.cartel) if jessica.cartel else 0} lutas")
            if jessica.cartel and len(jessica.cartel) > 0:
                victories = sum(1 for f in jessica.cartel if f.get("result") == "W")
                losses = sum(1 for f in jessica.cartel if f.get("result") == "L")
                print(f"   • Vitórias: {victories} | Derrotas: {losses}")

        print("\n" + "=" * 60)
        print("✅ VALIDAÇÃO CONCLUÍDA COM SUCESSO!")

    except Exception as e:
        print(f"\n❌ Erro durante validação: {str(e)}")
        raise

    finally:
        session.close()


if __name__ == "__main__":
    test_import()
