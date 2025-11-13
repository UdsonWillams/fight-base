"""
Script de importação do dataset UFC completo
Importa dados de events, fights e fighters mantendo relacionamentos via IDs
"""

import csv
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

# Adicionar o diretório raiz ao path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.settings import Settings
from app.database.models.base import Event, Fight, Fighter, User

settings = Settings()


class UFCDatasetImporter:
    """Importador do dataset UFC com mapeamento de IDs"""

    def __init__(self, db_session):
        self.session = db_session

        # Mapas para converter IDs do ufcstats para UUIDs do banco
        self.fighter_id_map: Dict[str, uuid.UUID] = {}
        self.event_id_map: Dict[str, uuid.UUID] = {}
        self.fight_id_map: Dict[str, uuid.UUID] = {}

        # Estatísticas de importação
        self.stats = {
            "fighters_created": 0,
            "fighters_updated": 0,
            "events_created": 0,
            "fights_created": 0,
            "errors": [],
        }

    def get_or_create_system_user(self) -> User:
        """Obtém ou cria usuário do sistema para criação de lutadores reais"""
        user = self.session.query(User).filter_by(email="system@fightbase.com").first()
        if not user:
            user = User(
                email="system@fightbase.com",
                password="system_no_login",
                name="System",
                role="admin",
                is_active=False,
                created_by="system",
                updated_by="system",
            )
            self.session.add(user)
            self.session.commit()
            print("✓ Usuário do sistema criado")
        return user

    def parse_date(self, date_str: str) -> Optional[datetime]:
        """Converte string de data para datetime"""
        if not date_str or date_str.strip() == "":
            return None

        try:
            # Formato: "September 06, 2025" ou "May 08, 1982"
            return datetime.strptime(date_str.strip(), "%B %d, %Y").replace(
                tzinfo=timezone.utc
            )
        except ValueError:
            try:
                # Tentar outros formatos comuns
                return datetime.strptime(date_str.strip(), "%Y-%m-%d").replace(
                    tzinfo=timezone.utc
                )
            except ValueError:
                return None

    def safe_float(self, value: str) -> Optional[float]:
        """Converte string para float com tratamento de erros"""
        if not value or value.strip() == "" or value.strip() == "--":
            return None
        try:
            return float(value.strip())
        except (ValueError, AttributeError):
            return None

    def safe_int(self, value: str) -> Optional[int]:
        """Converte string para int com tratamento de erros"""
        if not value or value.strip() == "" or value.strip() == "--":
            return None
        try:
            return int(float(value.strip()))
        except (ValueError, AttributeError):
            return None

    def parse_time_to_seconds(self, time_str: str) -> Optional[int]:
        """Converte tempo MM:SS para segundos totais"""
        if not time_str or time_str.strip() == "":
            return None
        try:
            parts = time_str.split(":")
            if len(parts) == 2:
                minutes = int(parts[0])
                seconds = int(parts[1])
                return minutes * 60 + seconds
        except Exception:
            return None
        return None

    def import_fighters(self, csv_path: str, system_user: User):
        """Importa lutadores do fighter_details.csv"""
        print(f"\n📥 Importando lutadores de {csv_path}...")

        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row in reader:
                try:
                    ufcstats_id = row["id"].strip()

                    # Verificar se já existe
                    existing = (
                        self.session.query(Fighter)
                        .filter_by(ufcstats_id=ufcstats_id)
                        .first()
                    )

                    # Converter altura e alcance de cm
                    height_cm = self.safe_float(row.get("height"))
                    reach_cm = self.safe_float(row.get("reach"))

                    # Calcular atributos baseados nas estatísticas
                    slpm = self.safe_float(row.get("splm"))
                    str_acc = self.safe_float(row.get("str_acc"))
                    sapm = self.safe_float(row.get("sapm"))
                    str_def = self.safe_float(row.get("str_def"))
                    td_avg = self.safe_float(row.get("td_avg"))
                    td_acc = self.safe_float(row.get("td_avg_acc"))
                    td_def = self.safe_float(row.get("td_def"))
                    sub_avg = self.safe_float(row.get("sub_avg"))

                    # Calcular atributos de 0-100 baseados nas stats
                    striking = min(100, int((slpm or 0) * 10 + (str_acc or 50)))
                    grappling = min(
                        100, int((td_avg or 0) * 20 + (sub_avg or 0) * 30 + 30)
                    )
                    defense = min(100, int((str_def or 50) + (td_def or 50)) // 2)

                    wins = self.safe_int(row.get("wins")) or 0
                    losses = self.safe_int(row.get("losses")) or 0
                    total_fights = wins + losses

                    # Estimar stamina baseado no histórico
                    stamina = min(100, 50 + total_fights)
                    speed = min(100, int((slpm or 3) * 15))
                    strategy = min(100, 50 + total_fights // 2)

                    fighter_data = {
                        "ufcstats_id": ufcstats_id,
                        "name": row["name"].strip(),
                        "nickname": row.get("nick_name", "").strip() or None,
                        "date_of_birth": self.parse_date(row.get("dob")),
                        "stance": row.get("stance", "").strip() or None,
                        "height_cm": height_cm,
                        "reach_cm": reach_cm,
                        "weight_lbs": self.safe_float(row.get("weight")),
                        "wins": wins,
                        "losses": losses,
                        "draws": self.safe_int(row.get("draws")) or 0,
                        "slpm": slpm,
                        "str_acc": str_acc,
                        "sapm": sapm,
                        "str_def": str_def,
                        "td_avg": td_avg,
                        "td_acc": td_acc,
                        "td_def": td_def,
                        "sub_avg": sub_avg,
                        "striking": striking,
                        "grappling": grappling,
                        "defense": defense,
                        "stamina": stamina,
                        "speed": speed,
                        "strategy": strategy,
                        "is_real": True,
                        "last_organization_fight": "UFC",
                        "creator_id": system_user.id,
                        "updated_by": "import_script",
                    }

                    if existing:
                        # Atualizar lutador existente
                        for key, value in fighter_data.items():
                            if key != "creator_id":  # Não alterar o criador
                                setattr(existing, key, value)
                        self.fighter_id_map[ufcstats_id] = existing.id
                        self.stats["fighters_updated"] += 1
                    else:
                        # Criar novo lutador
                        fighter = Fighter(**fighter_data)
                        self.session.add(fighter)
                        self.session.flush()
                        self.fighter_id_map[ufcstats_id] = fighter.id
                        self.stats["fighters_created"] += 1

                    if (
                        self.stats["fighters_created"] + self.stats["fighters_updated"]
                    ) % 100 == 0:
                        print(
                            f"  ⏳ Processados {self.stats['fighters_created'] + self.stats['fighters_updated']} lutadores..."
                        )
                        self.session.commit()

                except Exception as e:
                    error_msg = f"Erro ao importar lutador {row.get('name', 'Unknown')}: {str(e)}"
                    self.stats["errors"].append(error_msg)
                    print(f"  ⚠️  {error_msg}")
                    continue

            self.session.commit()

        print(
            f"✓ Lutadores importados: {self.stats['fighters_created']} criados, {self.stats['fighters_updated']} atualizados"
        )

    def import_events(self, csv_path: str, system_user: User):
        """Importa eventos do event_details.csv"""
        print(f"\n📥 Importando eventos de {csv_path}...")

        events_data = {}

        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row in reader:
                try:
                    event_id = row["event_id"].strip()

                    # Agrupar por evento
                    if event_id not in events_data:
                        events_data[event_id] = {
                            "location": row.get("location", "").strip(),
                            "date": self.parse_date(row.get("date")),
                            "fights": [],
                        }

                    # Adicionar luta ao evento
                    events_data[event_id]["fights"].append(
                        {
                            "fight_id": row["fight_id"].strip(),
                            "winner_id": row.get("winner_id", "").strip(),
                        }
                    )

                except Exception as e:
                    error_msg = f"Erro ao processar evento {row.get('event_id', 'Unknown')}: {str(e)}"
                    self.stats["errors"].append(error_msg)
                    print(f"  ⚠️  {error_msg}")
                    continue

        # Criar eventos
        for event_id, event_data in events_data.items():
            try:
                existing = (
                    self.session.query(Event).filter_by(ufcstats_id=event_id).first()
                )

                if not existing:
                    event = Event(
                        ufcstats_id=event_id,
                        name=f"UFC Event {event_id[:8]}",  # Nome temporário
                        date=event_data["date"] or datetime.now(timezone.utc),
                        location=event_data["location"],
                        organization="UFC",
                        status="completed",
                        creator_id=system_user.id,
                        created_by="import_script",
                        updated_by="import_script",
                    )
                    self.session.add(event)
                    self.session.flush()
                    self.event_id_map[event_id] = event.id
                    self.stats["events_created"] += 1
                else:
                    self.event_id_map[event_id] = existing.id

            except Exception as e:
                error_msg = f"Erro ao criar evento {event_id}: {str(e)}"
                self.stats["errors"].append(error_msg)
                print(f"  ⚠️  {error_msg}")
                continue

        self.session.commit()
        print(f"✓ Eventos importados: {self.stats['events_created']}")

    def import_fights(self, csv_path: str):
        """Importa lutas do fight_details.csv"""
        print(f"\n📥 Importando lutas de {csv_path}...")

        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            fight_order = {}  # Para rastrear ordem das lutas por evento

            for row in reader:
                try:
                    fight_id = row["fight_id"].strip()
                    event_id = row["event_id"].strip()

                    # Verificar se já existe
                    existing = (
                        self.session.query(Fight)
                        .filter_by(ufcstats_id=fight_id)
                        .first()
                    )

                    if existing:
                        continue

                    # Mapear IDs
                    r_id = row.get("r_id", "").strip()
                    b_id = row.get("b_id", "").strip()

                    if (
                        r_id not in self.fighter_id_map
                        or b_id not in self.fighter_id_map
                    ):
                        continue

                    if event_id not in self.event_id_map:
                        continue

                    fighter1_uuid = self.fighter_id_map[r_id]
                    fighter2_uuid = self.fighter_id_map[b_id]
                    event_uuid = self.event_id_map[event_id]

                    # Determinar ordem da luta no evento
                    if event_uuid not in fight_order:
                        fight_order[event_uuid] = 1
                    else:
                        fight_order[event_uuid] += 1

                    # Obter método da luta
                    method = row.get("method", "").strip()

                    # Normalizar método
                    result_type = None
                    if "KO" in method or "TKO" in method:
                        result_type = "KO/TKO"
                    elif "Submission" in method or "Sub" in method:
                        result_type = "Submission"
                    elif "Decision" in method:
                        result_type = "Decision"
                    elif "Draw" in method:
                        result_type = "Draw"

                    fight_data = {
                        "ufcstats_id": fight_id,
                        "event_id": event_uuid,
                        "fighter1_id": fighter1_uuid,
                        "fighter2_id": fighter2_uuid,
                        "fight_order": fight_order[event_uuid],
                        "weight_class": row.get("division", "").strip() or None,
                        "rounds": self.safe_int(row.get("total_rounds")) or 3,
                        "is_title_fight": bool(self.safe_int(row.get("title_fight"))),
                        "result_type": result_type,
                        "finish_round": self.safe_int(row.get("finish_round")),
                        "match_time_seconds": self.safe_int(row.get("match_time_sec")),
                        "referee": row.get("referee", "").strip() or None,
                        "method_details": method,
                        "status": "completed",
                        # Estatísticas Red Corner (fighter1)
                        "r_kd": self.safe_int(row.get("r_kd")),
                        "r_sig_str_landed": self.safe_int(row.get("r_sig_str_landed")),
                        "r_sig_str_attempted": self.safe_int(
                            row.get("r_sig_str_atmpted")
                        ),
                        "r_total_str_landed": self.safe_int(
                            row.get("r_total_str_landed")
                        ),
                        "r_total_str_attempted": self.safe_int(
                            row.get("r_total_str_atmpted")
                        ),
                        "r_td_landed": self.safe_int(row.get("r_td_landed")),
                        "r_td_attempted": self.safe_int(row.get("r_td_atmpted")),
                        "r_sub_att": self.safe_int(row.get("r_sub_att")),
                        "r_ctrl_seconds": self.parse_time_to_seconds(
                            row.get("r_ctrl", "")
                        ),
                        # Estatísticas Blue Corner (fighter2)
                        "b_kd": self.safe_int(row.get("b_kd")),
                        "b_sig_str_landed": self.safe_int(row.get("b_sig_str_landed")),
                        "b_sig_str_attempted": self.safe_int(
                            row.get("b_sig_str_atmpted")
                        ),
                        "b_total_str_landed": self.safe_int(
                            row.get("b_total_str_landed")
                        ),
                        "b_total_str_attempted": self.safe_int(
                            row.get("b_total_str_atmpted")
                        ),
                        "b_td_landed": self.safe_int(row.get("b_td_landed")),
                        "b_td_attempted": self.safe_int(row.get("b_td_atmpted")),
                        "b_sub_att": self.safe_int(row.get("b_sub_att")),
                        "b_ctrl_seconds": self.parse_time_to_seconds(
                            row.get("b_ctrl", "")
                        ),
                        "created_by": "import_script",
                        "updated_by": "import_script",
                    }

                    fight = Fight(**fight_data)
                    self.session.add(fight)
                    self.fight_id_map[fight_id] = fight.id
                    self.stats["fights_created"] += 1

                    if self.stats["fights_created"] % 100 == 0:
                        print(
                            f"  ⏳ Processadas {self.stats['fights_created']} lutas..."
                        )
                        self.session.commit()

                except Exception as e:
                    error_msg = f"Erro ao importar luta {row.get('fight_id', 'Unknown')}: {str(e)}"
                    self.stats["errors"].append(error_msg)
                    print(f"  ⚠️  {error_msg}")
                    continue

            self.session.commit()

        print(f"✓ Lutas importadas: {self.stats['fights_created']}")

    def populate_fight_winners(self, csv_path: str = "UFC.csv"):
        """Popula o campo winner_id das lutas baseado no UFC.csv"""
        print(f"\n🏆 Populando vencedores das lutas de {csv_path}...")

        try:
            import pandas as pd

            df = pd.read_csv(csv_path)

            updated_count = 0
            no_winner_count = 0
            not_found_count = 0

            for _, row in df.iterrows():
                fight_id = str(row.get("fight_id", "")).strip()
                winner_name = str(row.get("winner", "")).strip()
                r_name = str(row.get("r_name", "")).strip()  # Red corner (fighter1)
                b_name = str(row.get("b_name", "")).strip()  # Blue corner (fighter2)

                if not fight_id or fight_id == "nan":
                    continue

                # Buscar luta no banco
                fight = (
                    self.session.query(Fight).filter_by(ufcstats_id=fight_id).first()
                )

                if not fight:
                    not_found_count += 1
                    continue

                # Determinar winner_id baseado no nome do vencedor
                if winner_name and winner_name != "nan":
                    if winner_name == r_name:
                        # Red corner (fighter1) venceu
                        fight.winner_id = fight.fighter1_id
                        updated_count += 1
                    elif winner_name == b_name:
                        # Blue corner (fighter2) venceu
                        fight.winner_id = fight.fighter2_id
                        updated_count += 1
                    else:
                        # Nome não bate - pode ser empate ou NC
                        no_winner_count += 1
                else:
                    # Sem vencedor - empate ou NC
                    no_winner_count += 1

                if (updated_count + no_winner_count) % 500 == 0:
                    self.session.commit()

            self.session.commit()

            print("✓ Vencedores populados:")
            print(f"  • {updated_count} lutas com vencedor definido")
            print(f"  • {no_winner_count} lutas sem vencedor (empate/NC)")
            if not_found_count > 0:
                print(f"  ⚠️  {not_found_count} lutas não encontradas no banco")

        except ImportError:
            print("⚠️  Pandas não disponível. Pulando população de vencedores.")
            print("   Execute: pip install pandas")
        except Exception as e:
            print(f"❌ Erro ao popular vencedores: {str(e)}")
            self.session.rollback()

    def update_fighter_cartels(self):
        """Atualiza o cartel de cada lutador com base nas lutas importadas"""
        print("\n📊 Atualizando cartel dos lutadores...")

        fighters = (
            self.session.query(Fighter).filter(Fighter.ufcstats_id.isnot(None)).all()
        )

        for fighter in fighters:
            try:
                # Buscar todas as lutas do lutador com informações do evento
                fights = (
                    self.session.query(Fight, Event)
                    .join(Event, Fight.event_id == Event.id)
                    .filter(
                        (Fight.fighter1_id == fighter.id)
                        | (Fight.fighter2_id == fighter.id),
                        Fight.status == "completed",
                    )
                    .order_by(Event.date.desc())
                    .all()
                )

                cartel = []
                for fight, event in fights:
                    # Determinar se é fighter1 ou fighter2
                    is_fighter1 = fight.fighter1_id == fighter.id
                    opponent_id = (
                        fight.fighter2_id if is_fighter1 else fight.fighter1_id
                    )

                    opponent = self.session.query(Fighter).get(opponent_id)

                    # Determinar resultado
                    result = "N/A"
                    if fight.result_type == "Draw":
                        result = "D"
                    elif fight.winner_id:
                        if fight.winner_id == fighter.id:
                            result = "W"
                        else:
                            result = "L"

                    cartel_entry = {
                        "opponent": opponent.name if opponent else "Unknown",
                        "result": result,
                        "method": fight.result_type or "Unknown",
                        "round": fight.finish_round,
                        "date": event.date.strftime("%d/%m/%Y") if event.date else None,
                        "organization": "UFC",
                    }

                    cartel.append(cartel_entry)

                fighter.cartel = cartel

            except Exception as e:
                error_msg = f"Erro ao atualizar cartel de {fighter.name}: {str(e)}"
                self.stats["errors"].append(error_msg)
                print(f"  ⚠️  {error_msg}")
                continue

        self.session.commit()
        print(f"✓ Cartéis atualizados para {len(fighters)} lutadores")

    def update_event_names(self):
        """Atualiza nomes dos eventos usando o fight_details.csv"""
        print("\n📝 Atualizando nomes dos eventos...")

        # Ler nomes de eventos do fight_details.csv
        with open("datasets/fight_details.csv", "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            event_names = {}

            for row in reader:
                event_id = row["event_id"].strip()
                event_name = row.get("event_name", "").strip()

                if event_name and event_id not in event_names:
                    event_names[event_id] = event_name

        # Atualizar eventos no banco
        for ufcstats_id, name in event_names.items():
            if ufcstats_id in self.event_id_map:
                event_uuid = self.event_id_map[ufcstats_id]
                event = self.session.query(Event).get(event_uuid)
                if event:
                    event.name = name

        self.session.commit()
        print(f"✓ Nomes atualizados para {len(event_names)} eventos")

    def update_weight_classes(self):
        """Atualiza categorias de peso dos lutadores baseado nas lutas do UFC.csv"""
        print("\n📊 Atualizando categorias de peso dos lutadores...")

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
        print(
            f"  📋 Total de lutadores com categoria no CSV: {len(fighter_weight_classes)}"
        )

        for fighter_name, (weight_class, _) in fighter_weight_classes.items():
            # Buscar lutador pelo nome
            fighter = (
                self.session.query(Fighter).filter(Fighter.name == fighter_name).first()
            )
            if fighter:
                fighter.actual_weight_class = weight_class
                updated += 1
            else:
                not_found += 1
                if not_found <= 5:  # Mostrar apenas os 5 primeiros não encontrados
                    print(f"  ⚠️  Lutador não encontrado: {fighter_name}")

        self.session.commit()
        print(f"✓ Categorias de peso atualizadas para {updated} lutadores")
        if not_found > 0:
            print(f"  ⚠️  {not_found} lutadores não encontrados no banco")

    def print_stats(self):
        """Imprime estatísticas finais da importação"""
        print("\n" + "=" * 60)
        print("📊 ESTATÍSTICAS DA IMPORTAÇÃO")
        print("=" * 60)
        print(f"✓ Lutadores criados:     {self.stats['fighters_created']}")
        print(f"✓ Lutadores atualizados: {self.stats['fighters_updated']}")
        print(f"✓ Eventos criados:       {self.stats['events_created']}")
        print(f"✓ Lutas criadas:         {self.stats['fights_created']}")

        if self.stats["errors"]:
            print(f"\n⚠️  Erros encontrados:    {len(self.stats['errors'])}")
            print("\nPrimeiros 10 erros:")
            for error in self.stats["errors"][:10]:
                print(f"  - {error}")

        print("=" * 60)


def main():
    """Função principal de importação"""
    print("🥊 IMPORTADOR DE DATASET UFC")
    print("=" * 60)

    # Conectar ao banco
    engine = create_engine(settings.DATABASE_URL_SYNC)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Criar importador
        importer = UFCDatasetImporter(session)

        # Obter usuário do sistema
        system_user = importer.get_or_create_system_user()

        # 1. Importar lutadores primeiro (necessário para foreign keys)
        importer.import_fighters("datasets/fighter_details.csv", system_user)

        # 2. Importar eventos
        importer.import_events("datasets/event_details.csv", system_user)

        # 3. Importar lutas (requer lutadores e eventos já importados)
        importer.import_fights("datasets/fight_details.csv")

        # 4. Popular vencedores das lutas (requer lutas já importadas)
        importer.populate_fight_winners("datasets/UFC.csv")

        # 5. Atualizar nomes dos eventos
        importer.update_event_names()

        # 6. Atualizar cartel dos lutadores (requer vencedores já populados)
        importer.update_fighter_cartels()

        # 7. Atualizar categorias de peso dos lutadores
        importer.update_weight_classes()

        # Estatísticas finais
        importer.print_stats()

        print("\n✅ Importação concluída com sucesso!")

    except Exception as e:
        print(f"\n❌ Erro crítico durante importação: {str(e)}")
        session.rollback()
        raise

    finally:
        session.close()


if __name__ == "__main__":
    main()
