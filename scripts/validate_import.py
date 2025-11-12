"""
Script de validação dos dados importados do UFC Dataset
Verifica integridade e qualidade dos dados
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

from app.core.settings import Settings
from app.database.models.base import Fighter, Event, Fight

settings = Settings()
engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
Session = sessionmaker(bind=engine)


def validate_import():
    """Valida dados importados"""
    
    session = Session()
    
    print("🔍 VALIDAÇÃO DO DATASET IMPORTADO\n")
    print("=" * 60)
    
    issues = []
    warnings = []
    
    # 1. Contagem de registros
    print("\n📊 Contagem de Registros")
    print("-" * 60)
    
    fighters_count = session.query(func.count(Fighter.id)).filter(
        Fighter.ufcstats_id.isnot(None)
    ).scalar()
    print(f"✓ Lutadores com ufcstats_id: {fighters_count}")
    
    events_count = session.query(func.count(Event.id)).filter(
        Event.ufcstats_id.isnot(None)
    ).scalar()
    print(f"✓ Eventos com ufcstats_id:   {events_count}")
    
    fights_count = session.query(func.count(Fight.id)).filter(
        Fight.ufcstats_id.isnot(None)
    ).scalar()
    print(f"✓ Lutas com ufcstats_id:     {fights_count}")
    
    if fighters_count == 0:
        issues.append("❌ Nenhum lutador importado!")
    
    if events_count == 0:
        issues.append("❌ Nenhum evento importado!")
    
    if fights_count == 0:
        issues.append("❌ Nenhuma luta importada!")
    
    # 2. Validar relacionamentos
    print("\n🔗 Validação de Relacionamentos")
    print("-" * 60)
    
    orphan_fights = session.query(func.count(Fight.id)).filter(
        Fight.event_id.is_(None)
    ).scalar()
    
    if orphan_fights > 0:
        issues.append(f"❌ {orphan_fights} lutas sem evento!")
    else:
        print("✓ Todas as lutas têm evento associado")
    
    fights_without_fighters = session.query(func.count(Fight.id)).filter(
        (Fight.fighter1_id.is_(None)) | (Fight.fighter2_id.is_(None))
    ).scalar()
    
    if fights_without_fighters > 0:
        issues.append(f"❌ {fights_without_fighters} lutas sem lutadores!")
    else:
        print("✓ Todas as lutas têm lutadores associados")
    
    # 3. Validar dados dos lutadores
    print("\n👤 Validação de Dados dos Lutadores")
    print("-" * 60)
    
    fighters_without_stats = session.query(func.count(Fighter.id)).filter(
        Fighter.ufcstats_id.isnot(None),
        Fighter.slpm.is_(None)
    ).scalar()
    
    if fighters_without_stats > 0:
        warnings.append(f"⚠️  {fighters_without_stats} lutadores sem SLPM")
    else:
        print("✓ Todos os lutadores têm SLPM")
    
    fighters_without_dob = session.query(func.count(Fighter.id)).filter(
        Fighter.ufcstats_id.isnot(None),
        Fighter.date_of_birth.is_(None)
    ).scalar()
    
    if fighters_without_dob > 0:
        warnings.append(f"⚠️  {fighters_without_dob} lutadores sem data de nascimento")
    else:
        print("✓ Todos os lutadores têm data de nascimento")
    
    # 4. Validar cartéis
    print("\n🏆 Validação de Cartéis")
    print("-" * 60)
    
    fighters_with_cartel = session.query(func.count(Fighter.id)).filter(
        Fighter.ufcstats_id.isnot(None),
        Fighter.cartel != []
    ).scalar()
    
    print(f"✓ Lutadores com cartel: {fighters_with_cartel}/{fighters_count}")
    
    if fighters_with_cartel == 0:
        warnings.append("⚠️  Nenhum lutador tem cartel preenchido")
    
    # 5. Validar estatísticas das lutas
    print("\n📈 Validação de Estatísticas das Lutas")
    print("-" * 60)
    
    fights_with_stats = session.query(func.count(Fight.id)).filter(
        Fight.ufcstats_id.isnot(None),
        Fight.r_sig_str_landed.isnot(None)
    ).scalar()
    
    print(f"✓ Lutas com estatísticas: {fights_with_stats}/{fights_count}")
    
    if fights_with_stats < fights_count * 0.5:
        warnings.append(f"⚠️  Apenas {fights_with_stats}/{fights_count} lutas têm estatísticas")
    
    fights_with_referee = session.query(func.count(Fight.id)).filter(
        Fight.ufcstats_id.isnot(None),
        Fight.referee.isnot(None)
    ).scalar()
    
    print(f"✓ Lutas com árbitro: {fights_with_referee}/{fights_count}")
    
    # 6. Validar atributos calculados
    print("\n⚙️  Validação de Atributos Calculados")
    print("-" * 60)
    
    fighters_invalid_attrs = session.query(func.count(Fighter.id)).filter(
        Fighter.ufcstats_id.isnot(None),
        (Fighter.striking < 0) | (Fighter.striking > 100) |
        (Fighter.grappling < 0) | (Fighter.grappling > 100) |
        (Fighter.defense < 0) | (Fighter.defense > 100)
    ).scalar()
    
    if fighters_invalid_attrs > 0:
        issues.append(f"❌ {fighters_invalid_attrs} lutadores com atributos inválidos!")
    else:
        print("✓ Todos os atributos estão no intervalo [0, 100]")
    
    # 7. Validar nomes dos eventos
    print("\n🎪 Validação de Eventos")
    print("-" * 60)
    
    events_with_name = session.query(func.count(Event.id)).filter(
        Event.ufcstats_id.isnot(None),
        Event.name.isnot(None),
        Event.name != ''
    ).scalar()
    
    print(f"✓ Eventos com nome: {events_with_name}/{events_count}")
    
    if events_with_name < events_count:
        warnings.append(f"⚠️  {events_count - events_with_name} eventos sem nome")
    
    # Resultado final
    print("\n" + "=" * 60)
    print("📋 RESULTADO DA VALIDAÇÃO")
    print("=" * 60)
    
    if not issues and not warnings:
        print("\n✅ TODOS OS TESTES PASSARAM!")
        print("   Dataset importado com sucesso e sem problemas.")
    else:
        if issues:
            print("\n❌ PROBLEMAS CRÍTICOS ENCONTRADOS:")
            for issue in issues:
                print(f"   {issue}")
        
        if warnings:
            print("\n⚠️  AVISOS (Não Críticos):")
            for warning in warnings:
                print(f"   {warning}")
        
        if not issues:
            print("\n✅ Importação bem-sucedida com alguns avisos.")
        else:
            print("\n⚠️  Importação pode estar incompleta.")
    
    print("\n" + "=" * 60)
    
    session.close()
    
    # Retornar código de saída apropriado
    return 0 if not issues else 1


if __name__ == "__main__":
    exit_code = validate_import()
    sys.exit(exit_code)
