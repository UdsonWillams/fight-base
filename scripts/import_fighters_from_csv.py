"""
Script para importar lutadores a partir de um arquivo CSV.

Uso:
    python scripts/import_fighters_from_csv.py <caminho_do_csv>

Exemplo:
    python scripts/import_fighters_from_csv.py data/fighters.csv
"""

import asyncio
import csv
import sys
from pathlib import Path
from uuid import uuid4

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database.models.base import Fighter
from app.database.unit_of_work import UnitOfWorkConnection


def parse_height(height_str: str) -> float:
    """Converte altura de formato 'X.YY' (feet.inches) para centímetros."""
    if not height_str or height_str == "nan":
        return None
    try:
        feet, inches = height_str.split(".")
        total_inches = (int(feet) * 12) + int(inches)
        return round(total_inches * 2.54, 2)  # Converte para cm
    except:
        return None


def parse_weight(weight_str: str) -> float:
    """Converte peso de libras para quilos (opcional)."""
    if not weight_str or weight_str == "nan":
        return None
    try:
        return round(float(weight_str) * 0.453592, 2)  # Libras para kg
    except:
        return None


def parse_int(value: str, default: int = 0) -> int:
    """Converte string para int, retorna default se falhar."""
    if not value or value == "nan":
        return default
    try:
        return int(float(value))
    except:
        return default


def calculate_attributes(row: dict) -> dict:
    """
    Calcula os atributos de luta (0-100) baseado nas estatísticas do CSV.

    Baseado em:
    - Striking: STR (strikes por round), Sig. Str. %, KD (knockdowns), Head/Body/Leg distribution
    - Grappling: TD (takedowns), SUB (submissions), Ctrl (control time)
    - Defense: Baseado em % de defesa e reversões
    - Stamina: Baseado em rounds médios e controle
    - Speed: Baseado em strikes e distance %
    - Strategy: Baseado em diversidade de ataques e submission attempts
    """

    # Normaliza valores
    str_per_round = float(row.get("STR", 0) or 0)
    sig_str_pct = float(row.get("Sig. Str. %", 0) or 0)
    kd = float(row.get("KD", 0) or 0)
    td = float(row.get("TD", 0) or 0)
    sub = float(row.get("SUB", 0) or 0)  # ✅ AGORA USANDO!
    ctrl = float(row.get("Ctrl", 0) or 0)
    sub_att = float(row.get("Sub. Att", 0) or 0)
    rev = float(row.get("Rev.", 0) or 0)
    rounds = float(row.get("Round", 1) or 1)

    distance_pct = float(row.get("Distance_%", 0) or 0)
    clinch_pct = float(row.get("Clinch_%", 0) or 0)
    ground_pct = float(row.get("Ground_%", 0) or 0)

    # ✅ AGORA USANDO distribuição de strikes!
    head_pct = float(row.get("Head_%", 0) or 0)
    body_pct = float(row.get("Body_%", 0) or 0)
    leg_pct = float(row.get("Leg_%", 0) or 0)

    wins = parse_int(row.get("W", 0))
    losses = parse_int(row.get("L", 0))

    # STRIKING (0-100): Baseado em strikes por round, precisão, knockdowns e distribuição
    striking_base = min((str_per_round / 50) * 40, 40)  # Normaliza STR (50 é alto)
    striking_accuracy = sig_str_pct * 25  # Precisão vale até 25 pontos
    striking_power = min(kd * 5, 20)  # KDs valem até 20 pontos
    # ✅ NOVO: Diversidade de alvos (cabeça, corpo, perna) indica melhor striker
    striking_diversity = (
        (head_pct + body_pct + leg_pct) * 15
        if (head_pct + body_pct + leg_pct) > 0
        else 0
    )
    striking = min(
        int(striking_base + striking_accuracy + striking_power + striking_diversity),
        100,
    )

    # GRAPPLING (0-100): Baseado em takedowns, submissions, controle e ground %
    grappling_td = min((td / 3) * 35, 35)  # TD por round (3 é alto)
    grappling_sub = min(
        sub * 10, 25
    )  # ✅ NOVO: Submissions finalizadas valem até 25 pontos
    grappling_ctrl = min((ctrl / 120) * 25, 25)  # Control time (120s é alto)
    grappling_ground = ground_pct * 15  # Ground % vale até 15
    grappling = min(
        int(grappling_td + grappling_sub + grappling_ctrl + grappling_ground), 100
    )

    # DEFENSE (0-100): Baseado em reversões e % defensiva (inferida)
    defense_base = 50  # Base média
    defense_rev = min(rev * 10, 20)  # Reversões valem até 20
    # Se tem baixo striking contra si (inferido por vitórias), melhor defesa
    if wins > losses * 1.5:
        defense_record = 20
    elif wins > losses:
        defense_record = 10
    else:
        defense_record = 0
    defense = min(int(defense_base + defense_rev + defense_record), 100)

    # STAMINA (0-100): Baseado em rounds médios e controle prolongado
    stamina_rounds = min((rounds / 3) * 50, 50)  # 3 rounds é base
    stamina_ctrl = min((ctrl / 60) * 30, 30)  # Controle sustentado
    stamina_activity = min((str_per_round / 30) * 20, 20)  # Atividade constante
    stamina = min(int(stamina_rounds + stamina_ctrl + stamina_activity), 100)

    # SPEED (0-100): Baseado em volume de strikes e distance fighting
    speed_volume = min((str_per_round / 40) * 50, 50)
    speed_distance = distance_pct * 30  # Luta à distância requer velocidade
    speed_kd = min(kd * 10, 20)  # KDs rápidos
    speed = min(int(speed_volume + speed_distance + speed_kd), 100)

    # STRATEGY (0-100): Baseado em diversidade de técnicas e submissions
    strategy_diversity = (clinch_pct + ground_pct + distance_pct) * 20  # Max 60
    strategy_subs = min(sub_att * 10, 20)  # Tentativas de finalização
    strategy_record = min((wins / max(wins + losses, 1)) * 20, 20)  # Win rate
    strategy = min(int(strategy_diversity + strategy_subs + strategy_record), 100)

    return {
        "striking": max(30, striking),  # Mínimo 30
        "grappling": max(30, grappling),
        "defense": max(30, defense),
        "stamina": max(30, stamina),
        "speed": max(30, speed),
        "strategy": max(30, strategy),
    }


def map_weight_class(weight_class: str) -> str:
    """Mapeia classe de peso para formato padrão."""
    mapping = {
        "Heavyweight": "Heavyweight",
        "Light Heavyweight": "Light Heavyweight",
        "Middleweight": "Middleweight",
        "Welterweight": "Welterweight",
        "Lightweight": "Lightweight",
        "Featherweight": "Featherweight",
        "Bantamweight": "Bantamweight",
        "Flyweight": "Flyweight",
        "Women's Featherweight": "Women's Featherweight",
        "Women's Bantamweight": "Women's Bantamweight",
        "Women's Flyweight": "Women's Flyweight",
        "Women's Strawweight": "Women's Strawweight",
    }
    return mapping.get(weight_class, weight_class)


def map_fighting_style(style: str) -> str:
    """Mapeia estilo de luta."""
    mapping = {
        "Striker": "Striker",
        "Grappler": "Grappler",
        "Hybrid": "All-around",
    }
    return mapping.get(style, "All-around")


async def import_fighters(csv_path: str, creator_email: str = "system"):
    """Importa lutadores do CSV para o banco de dados."""

    print(f"📂 Lendo arquivo: {csv_path}")

    fighters = []

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            # Calcula atributos baseado nas estatísticas
            attributes = calculate_attributes(row)

            # Monta cartel
            wins = parse_int(row.get("W", 0))
            losses = parse_int(row.get("L", 0))
            draws = parse_int(row.get("D", 0))

            # Estima KO wins e Submission wins (se não vier nos dados)
            kd = float(row.get("KD", 0) or 0)
            sub_att = float(row.get("Sub. Att", 0) or 0)

            ko_wins = int(kd * 0.3 * wins) if kd > 0 else 0  # Estimativa
            submission_wins = int(sub_att * 0.2 * wins) if sub_att > 0 else 0

            cartel = []
            # Poderia adicionar lutas individuais aqui se tiver dados históricos

            fighter = Fighter(
                id=uuid4(),
                name=row.get("Full Name", "Unknown").strip(),
                nickname=row.get("Nickname", "").strip() or None,
                last_organization_fight="UFC",
                actual_weight_class=map_weight_class(
                    row.get("Weight_Class", "Unknown")
                ),
                fighting_style=map_fighting_style(row.get("Fighting Style", "Hybrid")),
                striking=attributes["striking"],
                grappling=attributes["grappling"],
                defense=attributes["defense"],
                stamina=attributes["stamina"],
                speed=attributes["speed"],
                strategy=attributes["strategy"],
                wins=wins,
                losses=losses,
                draws=draws,
                ko_wins=ko_wins,
                submission_wins=submission_wins,
                cartel=cartel,
                age=None,  # Não temos no CSV
                height_cm=parse_height(row.get("Ht.", "")),
                reach_cm=None,  # Não temos no CSV (poderia calcular estimativa baseado em altura)
                bio=(
                    f"Stance: {row.get('Stance', 'Unknown')}. "
                    f"Belt: {row.get('Belt', 'False')}. "
                    f"Weight: {row.get('Wt.', 'N/A')} lbs. "  # ✅ AGORA USANDO PESO NA BIO!
                    f"Strike Distribution - Head: {float(row.get('Head_%', 0) or 0):.0%}, "
                    f"Body: {float(row.get('Body_%', 0) or 0):.0%}, "
                    f"Leg: {float(row.get('Leg_%', 0) or 0):.0%}"
                ),
                image_url=None,
                is_real=True,
                creator_id=uuid4(),  # ID temporário do sistema
                created_by=creator_email,
            )

            fighters.append(fighter)

    print(f"✅ {len(fighters)} lutadores lidos do CSV")

    # Salva no banco
    print("💾 Salvando no banco de dados...")

    async with UnitOfWorkConnection() as uow:
        session = await uow.get_session()

        # Buscar ID do admin
        from sqlalchemy import select

        from app.database.models.base import User

        result = await session.execute(
            select(User).where(User.role == "admin").limit(1)
        )
        admin_user = result.scalar_one_or_none()

        if not admin_user:
            print("❌ Erro: Nenhum usuário admin encontrado!")
            print("Execute primeiro: python scripts/create_admin.py")
            return

        print(f"👤 Usando admin: {admin_user.email} (ID: {admin_user.id})")

        # Atualizar creator_id de todos os fighters e adicionar
        for fighter in fighters:
            fighter.creator_id = admin_user.id
            session.add(fighter)

        await uow.commit()

    print(f"✅ {len(fighters)} lutadores importados com sucesso!")

    # Mostra alguns exemplos
    print("\n📊 Exemplos de lutadores importados:")
    for fighter in fighters[:5]:
        print(f"  - {fighter.name} ({fighter.nickname})")
        print(f"    Cartel: {fighter.wins}-{fighter.losses}-{fighter.draws}")
        print(
            f"    Overall: {(fighter.striking + fighter.grappling + fighter.defense + fighter.stamina + fighter.speed + fighter.strategy) / 6:.1f}"
        )
        print(f"    Striking: {fighter.striking}, Grappling: {fighter.grappling}")


async def main():
    if len(sys.argv) < 2:
        print("❌ Erro: Forneça o caminho do arquivo CSV")
        print("Uso: python scripts/import_fighters_from_csv.py <caminho_do_csv>")
        sys.exit(1)

    csv_path = sys.argv[1]

    if not Path(csv_path).exists():
        print(f"❌ Erro: Arquivo não encontrado: {csv_path}")
        sys.exit(1)

    await import_fighters(csv_path)


if __name__ == "__main__":
    asyncio.run(main())
