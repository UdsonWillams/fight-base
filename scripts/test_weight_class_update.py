"""Script para testar atualização de categorias de peso"""

import csv
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.models.base import Fighter

# Configurar conexão
DATABASE_URL = "postgresql://myuser:mypassword@localhost:5432/fight_base"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

print("🔍 Testando atualização de categorias de peso...\n")

# Ler UFC.csv e mapear categoria de peso da última luta de cada lutador
fighter_weight_classes = {}

with open("datasets/UFC.csv", "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)

    for row in reader:
        date_str = row.get("date", "").strip()
        if not date_str:
            continue

        # Parse data
        try:
            fight_date = datetime.strptime(date_str, "%Y-%m-%d")
        except Exception:
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
                    fighter_weight_classes[fighter_name] = (division, fight_date)

print(f"📊 Total de lutadores com categoria no CSV: {len(fighter_weight_classes)}")

# Mostrar alguns exemplos
print("\n📋 Exemplos de lutadores com categorias:")
for i, (name, (division, date)) in enumerate(list(fighter_weight_classes.items())[:5]):
    print(f"  • {name}: {division} ({date.strftime('%Y-%m-%d')})")

# Testar busca de alguns lutadores específicos
test_names = ["Tom Aspinall", "Jessica Andrade", "Jon Jones"]
print("\n🔍 Testando busca de lutadores específicos:")
for name in test_names:
    fighter = session.query(Fighter).filter(Fighter.name == name).first()
    csv_data = fighter_weight_classes.get(name)
    if fighter:
        print(f"  ✓ {name}: encontrado no banco (ID: {fighter.id})")
        if csv_data:
            print(f"    → CSV tem: {csv_data[0]}")
        else:
            print("    ⚠️  Não encontrado no CSV")
    else:
        print(f"  ✗ {name}: NÃO encontrado no banco")
        if csv_data:
            print(f"    → CSV tem: {csv_data[0]}")

# Atualizar no banco
print("\n💾 Atualizando banco de dados...")
updated = 0
not_found = 0

for fighter_name, (weight_class, _) in fighter_weight_classes.items():
    fighter = session.query(Fighter).filter(Fighter.name == fighter_name).first()
    if fighter:
        fighter.actual_weight_class = weight_class
        updated += 1
    else:
        not_found += 1
        if not_found <= 10:
            print(f"  ⚠️  Não encontrado: {fighter_name}")

session.commit()

print("\n✅ Resultado:")
print(f"  • {updated} lutadores atualizados")
print(f"  • {not_found} lutadores não encontrados no banco")

# Verificar alguns lutadores após atualização
print("\n🔍 Verificando lutadores após atualização:")
for name in test_names:
    fighter = session.query(Fighter).filter(Fighter.name == name).first()
    if fighter:
        print(f"  • {name}: {fighter.actual_weight_class or '(vazio)'}")

session.close()
