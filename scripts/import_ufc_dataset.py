"""
Script de importação do dataset UFC completo.
Importa dados de events, fights e fighters mantendo relacionamentos via IDs.

Pipeline de importação (9 etapas executadas sequencialmente):
  1. import_fighters()   - Lê fighter_details.csv, cria/atualiza lutadores.
  2. import_events()     - Lê event_details.csv, cria eventos.
  3. import_fights()     - Lê fight_details.csv, cria lutas com estatísticas.
  4. populate_fight_winners() - Lê UFC.csv para definir winner_id de cada luta.
  5. update_fighter_ml_stats() - Agrega estatísticas por lutador (SLpM, TD avg, etc.).
  6. update_event_names() - Substitui nomes temporários por nomes reais dos eventos.
  7. update_fighter_cartels() - Constrói histórico de lutas (cartel) de cada lutador.
  8. update_weight_classes() - Define categoria de peso com base na luta mais recente.
  9. recalculate_fighter_attributes() - Recalcula os 6 atributos de jogo (striking,
     grappling, defense, stamina, speed, strategy) com dados agregados.

Os relacionamentos entre entidades são mantidos via IDs do UFC Stats,
mapeados para UUIDs internos do banco de dados. O script é idempotente:
lutas e lutadores já existentes são atualizados em vez de duplicados.
"""

import csv
import sys
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional


def _progress_log(label: str, done: int, total: int, start: float) -> None:
    """
    Imprime linha de progresso com tempo decorrido e estimativa de término (ETA).

    Parâmetros:
        label: Rótulo descritivo da etapa (ex.: "Lutadores").
        done: Quantidade de itens já processados.
        total: Quantidade total de itens a processar.
        start: Timestamp (time.time()) de início da etapa.

    Retorna:
        None (apenas efeito colateral de imprimir no console).
    """
    elapsed = time.time() - start
    pct = done / total * 100 if total else 0
    rate = done / elapsed if elapsed > 0 else 0
    remaining = (total - done) / rate if rate > 0 else 0
    mins_elapsed = int(elapsed // 60)
    secs_elapsed = int(elapsed % 60)
    mins_rem = int(remaining // 60)
    secs_rem = int(remaining % 60)
    print(
        f"  ⏳ {label}: {done:,}/{total:,} ({pct:.1f}%) — "
        f"⏱ {mins_elapsed}m{secs_elapsed:02d}s | ETA {mins_rem}m{secs_rem:02d}s"
    )

# Adiciona o diretório raiz ao path para permitir imports dos módulos 'app'
sys.path.append(str(Path(__file__).parent.parent))

# SQLAlchemy: engine para conexão e sessionmaker para criar sessões ORM
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Configurações (DATABASE_URL_SYNC) e modelos do banco de dados
from app.core.settings import Settings
from app.database.models.base import Event, Fight, Fighter, User

# Instância global de configurações carregadas do ambiente (.env)
settings = Settings()


class UFCDatasetImporter:
    """
    Importador principal do dataset UFC Stats.

    Responsável por ler os CSVs do dataset (fighter_details, event_details,
    fight_details, UFC.csv), converter dados, criar/atualizar registros no
    banco de dados via SQLAlchemy e manter mapas de IDs para resolver
    relacionamentos entre entidades.

    Atributos de instância:
        session (Session): Sessão SQLAlchemy ativa para transações.
        fighter_id_map (dict): Mapeia ufcstats_id (str) -> UUID do lutador.
        event_id_map (dict): Mapeia ufcstats_id (str) -> UUID do evento.
        fight_id_map (dict): Mapeia ufcstats_id (str) -> UUID da luta.
        stats (dict): Contadores de importação e lista de erros.
    """

    def __init__(self, db_session):
        """
        Inicializa o importador com uma sessão de banco ativa.

        Parâmetros:
            db_session: Sessão SQLAlchemy já conectada ao banco de dados.
        """
        self.session = db_session

        # Mapas para converter IDs do ufcstats (string) para UUIDs internos do banco.
        # Essenciais para resolver foreign keys entre fighters, events e fights.
        self.fighter_id_map: Dict[str, uuid.UUID] = {}
        self.event_id_map: Dict[str, uuid.UUID] = {}
        self.fight_id_map: Dict[str, uuid.UUID] = {}

        # Contadores de progresso e lista de erros para o relatório final
        self.stats = {
            "fighters_created": 0,
            "fighters_updated": 0,
            "events_created": 0,
            "fights_created": 0,
            "errors": [],
        }

        # Flag de cancelamento para interrupção entre steps
        self._cancelled = threading.Event()

    def cancel(self):
        """Sinaliza cancelamento da importação. Verificado entre steps da pipeline."""
        self._cancelled.set()

    def get_or_create_system_user(self) -> User:
        """
        Obtém ou cria o usuário do sistema usado como 'creator' dos registros.

        Retorna:
            User: O usuário 'system@fightbase.com', criado se não existir.
        """
        user = self.session.query(User).filter_by(email="system@fightbase.com").first()
        if not user:
            user = User(
                email="system@fightbase.com",
                username="admin",
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
        """
        Converte string de data para datetime UTC-aware.

        Parâmetros:
            date_str: String de data em um dos formatos suportados.

        Retorna:
            datetime com timezone UTC ou None se inválido/vazio.
        """
        if not date_str or date_str.strip() == "" or date_str.strip() == "--":
            return None

        date_str = date_str.strip()
        # O dataset UFC Stats pode usar diferentes formatos de data;
        # tenta cada um em ordem até conseguir parse.
        formats = [
            "%B %d, %Y",  # September 06, 2025
            "%b %d, %Y",  # Mar 09, 1985
            "%Y-%m-%d",    # 1985-03-09
            "%d/%m/%Y",    # 09/03/1985
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).replace(tzinfo=timezone.utc)
            except ValueError:
                continue

        return None

    def parse_height_to_cm(self, height_str: str) -> Optional[float]:
        """
        Converte altura do formato imperial (ex.: 5' 8") para centímetros.

        Parâmetros:
            height_str: String como "5' 8\"" ou "172.72" (já em cm).

        Retorna:
            Altura em centímetros (float com 2 casas decimais) ou None.
        """
        if not height_str or height_str.strip() == "" or height_str.strip() == "--":
            return None
        try:
            # Remove aspas e apóstrofos para normalizar o valor
            height_str = height_str.strip().replace('"', "").replace("'", " ")
            parts = height_str.split()

            if len(parts) == 2:
                # Formato pés + polegadas: converte cada unidade e soma.
                # 1 pé = 30.48 cm, 1 polegada = 2.54 cm
                feet = float(parts[0])
                inches = float(parts[1])
                return round((feet * 30.48) + (inches * 2.54), 2)
            elif len(parts) == 1:
                # Valor único: heurística para distinguir pés (< 10) de cm (>= 100).
                val = float(parts[0])
                if val < 10:  # Assumir pés se for um número pequeno
                    return round(val * 30.48, 2)
                return round(val, 2)
        except (ValueError, IndexError):
            return None
        return None

    def parse_reach_to_cm(self, reach_str: str) -> Optional[float]:
        """
        Converte alcance/envergadura de polegadas para centímetros.

        Parâmetros:
            reach_str: String como "68\"" (polegadas) ou "172.72" (já em cm).

        Retorna:
            Alcance em centímetros (float com 2 casas decimais) ou None.
        """
        if not reach_str or reach_str.strip() == "" or reach_str.strip() == "--":
            return None
        try:
            # Remove aspas para obter apenas o valor numérico
            reach_str = reach_str.strip().replace('"', "")
            val = float(reach_str)
            # No UFC Stats, alcance é dado em polegadas. Se > 100, já está em cm.
            # 1 polegada = 2.54 cm
            if val < 100:  # Assumir polegadas
                return round(val * 2.54, 2)
            return round(val, 2)
        except ValueError:
            return None

    def parse_weight_to_lbs(self, weight_str: str) -> Optional[float]:
        """
        Extrai peso numérico em libras de strings como '135 lbs.'.

        Parâmetros:
            weight_str: String como "135 lbs." ou "135".

        Retorna:
            Peso em libras (float) ou None se inválido/vazio.
        """
        if not weight_str or weight_str.strip() == "" or weight_str.strip() == "--":
            return None
        try:
            # Remove sufixo "lbs." e converte o valor numérico restante
            weight_str = weight_str.strip().lower().replace("lbs.", "").strip()
            return float(weight_str)
        except ValueError:
            return None

    def safe_float(self, value: str) -> Optional[float]:
        """
        Converte string para float com tratamento seguro de erros e valores vazios.

        Parâmetros:
            value: String numérica ou vazia/'--'.

        Retorna:
            Float convertido ou None se inválido/vazio.
        """
        if not value or value.strip() == "" or value.strip() == "--":
            return None
        try:
            return float(value.strip())
        except (ValueError, AttributeError):
            return None

    def safe_int(self, value: str) -> Optional[int]:
        """
        Converte string para int com tratamento seguro de erros e valores vazios.

        Parâmetros:
            value: String numérica ou vazia/'--'.

        Retorna:
            Int convertido (via float intermediário para suportar "3.0")
            ou None se inválido/vazio.
        """
        if not value or value.strip() == "" or value.strip() == "--":
            return None
        try:
            # Passa por float primeiro para aceitar valores como "3.0" no CSV
            return int(float(value.strip()))
        except (ValueError, AttributeError):
            return None

    def parse_time_to_seconds(self, time_str: str) -> Optional[int]:
        """
        Converte tempo em formato MM:SS ou numérico para segundos totais.

        Parâmetros:
            time_str: String como "12:34" (minutos:segundos) ou "754" (segundos).

        Retorna:
            Total de segundos (int) ou None se inválido/vazio.
        """
        if not time_str or time_str.strip() == "":
            return None
        s = time_str.strip()
        try:
            if ":" in s:
                # Formato MM:SS: minutos * 60 + segundos
                parts = s.split(":")
                if len(parts) == 2:
                    return int(parts[0]) * 60 + int(parts[1])
            # Valor numérico simples (já em segundos)
            return int(float(s))
        except Exception:
            return None

    def import_fighters(self, csv_path: str, system_user: User):
        """
        Importa lutadores do arquivo fighter_details.csv.

        Cria novos registros Fighter ou atualiza existentes (identificados por
        ufcstats_id). Converte medidas imperiais para métricas e calcula
        atributos iniciais de jogo (striking, grappling, etc.) com base nas
        estatísticas disponíveis no CSV.

        Parâmetros:
            csv_path: Caminho para o arquivo fighter_details.csv.
            system_user: Usuário do sistema usado como 'creator' dos registros.
        """
        # Contar total de linhas para o progresso (subtrai 1 do header)
        with open(csv_path, "r", encoding="utf-8") as f:
            total_rows = sum(1 for _ in f) - 1  # -1 para o header
        print(f"\n📥 Importando {total_rows:,} lutadores de {csv_path}...")
        start = time.time()

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

                    # Converter altura, peso e alcance usando novos parsers robustos
                    height_cm = self.parse_height_to_cm(row.get("height"))
                    reach_cm = self.parse_reach_to_cm(row.get("reach"))
                    weight_lbs = self.parse_weight_to_lbs(row.get("weight"))

                    # Calcular atributos baseados nas estatísticas (se existirem no CSV)
                    # NOTA: O CSV fighter_details.csv atual não possui essas colunas de stats avançadas
                    slpm = self.safe_float(row.get("splm"))
                    str_acc = self.safe_float(row.get("str_acc"))
                    sapm = self.safe_float(row.get("sapm"))
                    str_def = self.safe_float(row.get("str_def"))
                    td_avg = self.safe_float(row.get("td_avg"))
                    td_acc = self.safe_float(row.get("td_avg_acc"))
                    td_def = self.safe_float(row.get("td_def"))
                    sub_avg = self.safe_float(row.get("sub_avg"))

                    # Calcular atributos de 0-100 baseados nas estatísticas (escala agressiva).
                    # Cada fórmula combina métricas específicas com pesos empíricos
                    # para produzir um score de 0-100 no estilo "rating de jogo".
                    wins = self.safe_int(row.get("wins")) or 0
                    losses = self.safe_int(row.get("losses")) or 0
                    draws = self.safe_int(row.get("draws")) or 0
                    total_fights = wins + losses + draws
                    win_rate = (wins / total_fights * 100) if total_fights > 0 else 50

                    # Striking: volume de golpes (SLpM) + precisão (str_acc) + base
                    striking = min(100, int((slpm or 3) * 14 + (str_acc or 45) * 0.35 + 15))
                    # Grappling: quedas (td_avg) + submissões (sub_avg) + base
                    grappling = min(100, int((td_avg or 1) * 18 + (sub_avg or 0.2) * 30 + 10))
                    # Defense: defesa de golpes (str_def) + defesa de quedas (td_def)
                    defense = min(100, int((str_def or 50) * 0.6 + (td_def or 50) * 0.5))

                    # Stamina, speed e strategy levam em conta a experiência (total_fights)
                    # e a taxa de vitórias (win_rate) como indicadores de consistência
                    stamina = min(100, int(65 + total_fights * 0.8 + win_rate * 0.15))
                    speed = min(100, int((slpm or 3) * 14 + (str_acc or 45) * 0.3 + 10))
                    strategy = min(100, int(55 + total_fights * 0.5 + win_rate * 0.2))

                    # Monta dicionário com todos os campos do lutador para
                    # criação ou atualização em lote
                    fighter_data = {
                        "ufcstats_id": ufcstats_id,
                        "name": row["name"].strip(),
                        "nickname": row.get("nick_name", "").strip() or None,
                        "date_of_birth": self.parse_date(row.get("dob")),
                        "stance": row.get("stance", "").strip() or None,
                        "height_cm": height_cm,
                        "reach_cm": reach_cm,
                        "weight_lbs": weight_lbs,
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
                        # Atualizar lutador existente com os dados mais recentes.
                        # Preserva creator_id original para não sobrescrever o autor.
                        for key, value in fighter_data.items():
                            if key != "creator_id":
                                setattr(existing, key, value)
                        self.fighter_id_map[ufcstats_id] = existing.id
                        self.stats["fighters_updated"] += 1
                    else:
                        # Criar novo lutador e obter UUID via flush para o mapa de IDs
                        fighter = Fighter(**fighter_data)
                        self.session.add(fighter)
                        self.session.flush()
                        self.fighter_id_map[ufcstats_id] = fighter.id
                        self.stats["fighters_created"] += 1

                    done = self.stats["fighters_created"] + self.stats["fighters_updated"]
                    if done % 100 == 0:
                        _progress_log("Lutadores", done, total_rows, start)
                        self.session.commit()

                except Exception as e:
                    error_msg = f"Erro ao importar lutador {row.get('name', 'Unknown')}: {str(e)}"
                    self.stats["errors"].append(error_msg)
                    print(f"  ⚠️  {error_msg}")
                    continue

            self.session.commit()

        elapsed = time.time() - start
        print(
            f"✓ Lutadores importados em {int(elapsed//60)}m{int(elapsed%60):02d}s — "
            f"{self.stats['fighters_created']} criados, {self.stats['fighters_updated']} atualizados"
        )

    def import_events(self, csv_path: str, system_user: User):
        """
        Importa eventos do arquivo event_details.csv.

        Agrupa as linhas do CSV por event_id para extrair localização e data,
        depois cria registros Event no banco. Cada linha do CSV também contém
        o fight_id, usado para contagem de lutas por evento.

        Parâmetros:
            csv_path: Caminho para o arquivo event_details.csv.
            system_user: Usuário do sistema usado como 'creator' dos registros.
        """
        print(f"\n📥 Importando eventos de {csv_path}...")

        events_data = {}

        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row in reader:
                try:
                    event_id = row["event_id"].strip()

                    # Agrupa linhas do CSV por event_id para consolidar dados do evento
                    if event_id not in events_data:
                        raw_status = row.get("event_status", "completed")
                        events_data[event_id] = {
                            "location": row.get("location", "").strip(),
                            "date": self.parse_date(row.get("date")),
                            "fights": [],
                            "event_status": raw_status.strip() if raw_status else "completed",
                        }
                    else:
                        # If event was scraped as upcoming then re-scraped as completed, upgrade status
                        new_status = row.get("event_status", "").strip()
                        if events_data[event_id].get("event_status") == "upcoming" and new_status == "completed":
                            events_data[event_id]["event_status"] = "completed"

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
                    event_status = event_data.get("event_status", "completed")
                    if event_status == "upcoming":
                        event_status = "scheduled"
                    event = Event(
                        ufcstats_id=event_id,
                        name=f"UFC Event {event_id[:8]}",  # Nome temporário
                        date=event_data["date"] or datetime.now(timezone.utc),
                        location=event_data["location"],
                        organization="UFC",
                        status=event_status,
                        creator_id=system_user.id,
                        created_by="import_script",
                        updated_by="import_script",
                    )
                    self.session.add(event)
                    self.session.flush()
                    self.event_id_map[event_id] = event.id
                    self.stats["events_created"] += 1
                else:
                    # Update status if event changed from upcoming to completed
                    existing_event_status = event_data.get("event_status", "completed")
                    if existing_event_status == "upcoming":
                        existing_event_status = "scheduled"
                    if existing.status != existing_event_status:
                        existing.status = existing_event_status
                    self.event_id_map[event_id] = existing.id

            except Exception as e:
                error_msg = f"Erro ao criar evento {event_id}: {str(e)}"
                self.stats["errors"].append(error_msg)
                print(f"  ⚠️  {error_msg}")
                continue

        self.session.commit()
        print(f"✓ Eventos importados: {self.stats['events_created']}")

    def import_fights(self, csv_path: str):
        """
        Importa lutas do arquivo fight_details.csv.

        Usa abordagem em duas passadas:
        1. Conta quantas lutas cada evento tem (para calcular fight_order).
        2. Importa as lutas com fight_order decrescente (luta principal = 1).

        Também normaliza o método de vitória (KO/TKO, Submission, Decision, Draw)
        e popula estatísticas detalhadas para ambos os corners (red e blue).

        Parâmetros:
            csv_path: Caminho para o arquivo fight_details.csv.
        """
        with open(csv_path, "r", encoding="utf-8") as f:
            total_rows = sum(1 for _ in f) - 1
        print(f"\n📥 Importando {total_rows:,} lutas de {csv_path}...")
        start = time.time()

        # Build event_id -> status map from event_details.csv
        event_status_map = {}
        event_csv_path = str(Path(csv_path).parent / "event_details.csv")
        try:
            with open(event_csv_path, "r", encoding="utf-8") as f:
                ereader = csv.DictReader(f)
                for erow in ereader:
                    eid = erow.get("event_id", "").strip()
                    estatus = erow.get("event_status", "completed").strip()
                    if eid and eid not in event_status_map:
                        event_status_map[eid] = estatus
        except FileNotFoundError:
            pass

        # Primeira passada: contar quantas lutas cada evento tem.
        # Necessário para atribuir fight_order decrescente (main event = 1).
        event_fight_counts = {}
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                eid = row["event_id"].strip()
                if eid and eid in self.event_id_map:
                    event_fight_counts[eid] = event_fight_counts.get(eid, 0) + 1

        # Segunda passada: importar lutas com fight_order decrescente
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            fight_order = {}  # Rastreia a próxima ordem a atribuir por evento
            processed = 0

            for row in reader:
                processed += 1
                try:
                    fight_id = row["fight_id"].strip()
                    event_id = row["event_id"].strip()

                    if event_id not in self.event_id_map:
                        continue

                    event_uuid = self.event_id_map[event_id]

                    # Determinar ordem da luta no evento (decrescente: N, N-1, ..., 1).
                    # A primeira luta do evento recebe o número total de lutas,
                    # a última (main event) recebe 1. Calculado ANTES da verificação
                    # de existing para manter a sequência correta mesmo com updates.
                    if event_uuid not in fight_order:
                        total = event_fight_counts.get(event_id, 1)
                        fight_order[event_uuid] = total
                    else:
                        fight_order[event_uuid] -= 1

                    current_order = fight_order[event_uuid]

                    # Verificar se já existe - se existir, atualizar apenas fight_order
                    existing = (
                        self.session.query(Fight)
                        .filter_by(ufcstats_id=fight_id)
                        .first()
                    )

                    if existing:
                        existing.fight_order = current_order
                        # Update status if fight changed from scheduled to completed
                        event_status = event_status_map.get(event_id, "completed")
                        if event_status == "upcoming":
                            event_status = "scheduled"
                        existing.status = event_status
                        self.stats["fights_updated"] = self.stats.get("fights_updated", 0) + 1
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

                    # Obter método da luta e normalizar para categorias padronizadas
                    method = row.get("method", "").strip()

                    # Normaliza a string de método para um tipo canônico
                    result_type = None
                    if "KO" in method or "TKO" in method:
                        result_type = "KO/TKO"
                    elif "Submission" in method or "Sub" in method:
                        result_type = "Submission"
                    elif "Decision" in method:
                        result_type = "Decision"
                    elif "Draw" in method:
                        result_type = "Draw"

                    # Monta dicionário com todos os campos da luta, incluindo
                    # estatísticas de ambos os corners (r_ = red/fighter1, b_ = blue/fighter2)
                    fight_data = {
                        "ufcstats_id": fight_id,
                        "event_id": event_uuid,
                        "fighter1_id": fighter1_uuid,
                        "fighter2_id": fighter2_uuid,
                        "fight_order": current_order,
                        "weight_class": row.get("division", "").strip() or None,
                        "rounds": self.safe_int(row.get("total_rounds")) or 3,
                        "is_title_fight": bool(self.safe_int(row.get("title_fight"))),
                        "result_type": result_type,
                        "finish_round": self.safe_int(row.get("finish_round")),
                        "match_time_seconds": self.safe_int(row.get("match_time_sec")),
                        "referee": row.get("referee", "").strip() or None,
                        "method_details": method,
                        "status": event_status_map.get(event_id, "completed").replace("upcoming", "scheduled"),
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

                    if processed % 500 == 0:
                        _progress_log("Lutas", processed, total_rows, start)
                        self.session.commit()

                except Exception as e:
                    error_msg = f"Erro ao importar luta {row.get('fight_id', 'Unknown')}: {str(e)}"
                    self.stats["errors"].append(error_msg)
                    print(f"  ⚠️  {error_msg}")
                    continue

            self.session.commit()

        elapsed = time.time() - start
        print(
            f"✓ {self.stats['fights_created']:,} lutas importadas em "
            f"{int(elapsed//60)}m{int(elapsed%60):02d}s "
            f"({processed - self.stats['fights_created']:,} puladas por IDs não mapeados)"
        )

    def populate_fight_winners(self, csv_path: str = "UFC.csv"):
        """
        Popula o campo winner_id das lutas com base no arquivo UFC.csv.

        Compara o nome do vencedor no CSV com os nomes de red/blue corner
        para determinar se fighter1 ou fighter2 venceu. Usa pandas para
        leitura eficiente do CSV, com fallback silencioso se indisponível.

        Parâmetros:
            csv_path: Caminho para o arquivo UFC.csv (default: "UFC.csv").
        """
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

                # Skip fights that haven't happened yet
                if fight.status != "completed":
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
        """
        Atualiza o cartel (histórico de lutas) de cada lutador.

        Para cada lutador real, busca todas as suas lutas completadas,
        determina adversário, resultado (W/L/D), método, round e data,
        e armazena como lista de dicionários no campo 'cartel' (JSON).
        Também define last_fight_date com a data da luta mais recente.
        """
        fighters = (
            self.session.query(Fighter).filter(Fighter.ufcstats_id.isnot(None)).all()
        )
        total = len(fighters)
        print(f"\n📊 Atualizando cartel de {total:,} lutadores...")
        start = time.time()

        for i, fighter in enumerate(fighters, 1):
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
                    # Determinar se o lutador é fighter1 (red) ou fighter2 (blue)
                    is_fighter1 = fight.fighter1_id == fighter.id
                    opponent_id = (
                        fight.fighter2_id if is_fighter1 else fight.fighter1_id
                    )

                    opponent = self.session.get(Fighter, opponent_id)

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
                        "corner": "Red" if is_fighter1 else "Blue",
                    }

                    cartel.append(cartel_entry)

                fighter.cartel = cartel

                # Extrai a data da luta mais recente do cartel
                if fights:
                    fighter.last_fight_date = fights[0][1].date

                if i % 200 == 0:
                    _progress_log("Cartéis", i, total, start)
                    self.session.commit()

            except Exception as e:
                error_msg = f"Erro ao atualizar cartel de {fighter.name}: {str(e)}"
                self.stats["errors"].append(error_msg)
                print(f"  ⚠️  {error_msg}")
                continue

        self.session.commit()
        elapsed = time.time() - start
        print(f"✓ Cartéis atualizados para {total:,} lutadores em {int(elapsed//60)}m{int(elapsed%60):02d}s")

    def update_fighter_ml_stats(self):
        """
        Agrega estatísticas por luta para preencher métricas de ML e fighting_style.

        Para cada lutador real, varre todas as suas lutas completadas e acumula:
        - Totais de golpes significativos (landed/attempted), quedas, submissões,
          knockdowns, tempo de controle e tempo total de luta.
        - Contagem de vitórias por KO/TKO e Submission.

        Depois calcula as métricas por minuto/acurácia:
        - SLpM (Strikes Landed per Minute)
        - StrAcc (Striking Accuracy %)
        - SApM (Strikes Absorbed per Minute)
        - StrDef (Striking Defense %)
        - TDAvg (Takedowns per 15 min)
        - TDAcc (Takedown Accuracy %)
        - TDDef (Takedown Defense %)
        - SubAvg (Submissions per 15 min)

        Por fim classifica o fighting_style:
        - Striker: SLpM > 4.5 e TD avg < 1.5
        - Grappler: TD avg > 2.5 e SLpM < 3.5
        - MMA: demais casos
        """
        fighters = (
            self.session.query(Fighter).filter(Fighter.ufcstats_id.isnot(None)).all()
        )
        total = len(fighters)
        print(f"\n📊 Agregando ML stats para {total:,} lutadores...")
        start = time.time()
        updated = 0

        for i, fighter in enumerate(fighters, 1):
            try:
                fights = (
                    self.session.query(Fight)
                    .filter(
                        (Fight.fighter1_id == fighter.id)
                        | (Fight.fighter2_id == fighter.id),
                        Fight.status == "completed",
                    )
                    .all()
                )

                if not fights:
                    continue

                # Inicializa acumuladores para agregação das estatísticas
                total_sig_str_landed = 0
                total_sig_str_attempted = 0
                total_opp_sig_str_landed = 0
                total_opp_sig_str_attempted = 0
                total_td_landed = 0
                total_td_attempted = 0
                total_opp_td_landed = 0
                total_opp_td_attempted = 0
                total_sub_att = 0
                total_match_seconds = 0
                total_ctrl_seconds = 0
                total_kd_landed = 0
                ko_wins = 0
                submission_wins = 0

                for fight in fights:
                    is_f1 = fight.fighter1_id == fighter.id

                    sig_str_landed = fight.r_sig_str_landed if is_f1 else fight.b_sig_str_landed
                    sig_str_attempted = fight.r_sig_str_attempted if is_f1 else fight.b_sig_str_attempted
                    td_landed = fight.r_td_landed if is_f1 else fight.b_td_landed
                    td_attempted = fight.r_td_attempted if is_f1 else fight.b_td_attempted
                    sub_att = fight.r_sub_att if is_f1 else fight.b_sub_att

                    opp_sig_str_landed = fight.b_sig_str_landed if is_f1 else fight.r_sig_str_landed
                    opp_sig_str_attempted = fight.b_sig_str_attempted if is_f1 else fight.r_sig_str_attempted
                    opp_td_landed = fight.b_td_landed if is_f1 else fight.r_td_landed
                    opp_td_attempted = fight.b_td_attempted if is_f1 else fight.r_td_attempted

                    ctrl_sec = fight.r_ctrl_seconds if is_f1 else fight.b_ctrl_seconds
                    kd_val = fight.r_kd if is_f1 else fight.b_kd

                    if sig_str_landed is not None:
                        total_sig_str_landed += sig_str_landed
                    if sig_str_attempted is not None:
                        total_sig_str_attempted += sig_str_attempted
                    if opp_sig_str_landed is not None:
                        total_opp_sig_str_landed += opp_sig_str_landed
                    if opp_sig_str_attempted is not None:
                        total_opp_sig_str_attempted += opp_sig_str_attempted
                    if td_landed is not None:
                        total_td_landed += td_landed
                    if td_attempted is not None:
                        total_td_attempted += td_attempted
                    if opp_td_landed is not None:
                        total_opp_td_landed += opp_td_landed
                    if opp_td_attempted is not None:
                        total_opp_td_attempted += opp_td_attempted
                    if sub_att is not None:
                        total_sub_att += sub_att
                    if fight.match_time_seconds is not None:
                        total_match_seconds += fight.match_time_seconds
                    if ctrl_sec is not None:
                        total_ctrl_seconds += ctrl_sec
                    if kd_val is not None:
                        total_kd_landed += kd_val

                    method = (fight.method_details or "").lower()
                    if fight.winner_id == fighter.id:
                        if "ko" in method or "tko" in method:
                            ko_wins += 1
                        elif "submission" in method:
                            submission_wins += 1

                # --- Cálculo das métricas de ML a partir dos totais agregados ---

                # Total de minutos em luta (usado como denominador para taxas)
                total_match_minutes = total_match_seconds / 60 if total_match_seconds > 0 else 0

                # SLpM: golpes significativos desferidos por minuto
                slpm = round(total_sig_str_landed / total_match_minutes, 2) if total_match_minutes > 0 else None
                # StrAcc: precisão de golpes significativos (landed / attempted * 100)
                str_acc = (
                    round(total_sig_str_landed / total_sig_str_attempted * 100, 1)
                    if total_sig_str_attempted > 0
                    else None
                )
                # SApM: golpes significativos absorvidos por minuto (métrica defensiva)
                sapm = round(total_opp_sig_str_landed / total_match_minutes, 2) if total_match_minutes > 0 else None
                # StrDef: defesa de golpes = 100 - % de golpes do oponente que acertaram
                str_def = (
                    round(100 - (total_opp_sig_str_landed / total_opp_sig_str_attempted * 100), 1)
                    if total_opp_sig_str_attempted > 0
                    else None
                )
                # TDAvg: quedas por 15 minutos (padrão UFC Stats)
                td_avg = round(total_td_landed / (total_match_seconds / 900), 2) if total_match_seconds > 0 else None
                # TDAcc: precisão de quedas
                td_acc = (
                    round(total_td_landed / total_td_attempted * 100, 1)
                    if total_td_attempted > 0
                    else None
                )
                # TDDef: defesa de quedas = 100 - % de quedas do oponente que passaram
                td_def = (
                    round(100 - (total_opp_td_landed / total_opp_td_attempted * 100), 1)
                    if total_opp_td_attempted > 0
                    else None
                )
                # SubAvg: tentativas de submissão por 15 minutos
                sub_avg = round(total_sub_att / (total_match_seconds / 900), 2) if total_match_seconds > 0 else None

                # KD Avg: média de knockdowns por luta
                kd_avg = round(total_kd_landed / len(fights), 2) if fights else None

                # Ctrl Avg: tempo de controle (em segundos) por 15 minutos
                ctrl_avg = round(total_ctrl_seconds / (total_match_seconds / 900), 2) if total_match_seconds > 0 else None

                # --- Classificação do estilo de luta ---
                # Usa SLpM e TD avg como principais diferenciadores:
                #   Striker:  alto volume de golpes, poucas quedas
                #   Grappler: muitas quedas, baixo volume de golpes
                #   MMA:      perfil balanceado (ou dados insuficientes)
                if slpm is not None and td_avg is not None:
                    if slpm > 4.5 and td_avg < 1.5:
                        fighting_style = "Striker"
                    elif td_avg > 2.5 and slpm < 3.5:
                        fighting_style = "Grappler"
                    else:
                        fighting_style = "MMA"
                else:
                    fighting_style = "MMA"

                # Atualizar lutador
                fighter.slpm = slpm
                fighter.str_acc = str_acc
                fighter.sapm = sapm
                fighter.str_def = str_def
                fighter.td_avg = td_avg
                fighter.td_acc = td_acc
                fighter.td_def = td_def
                fighter.sub_avg = sub_avg
                fighter.kd_avg = kd_avg
                fighter.ctrl_avg = ctrl_avg
                fighter.ko_wins = ko_wins or None
                fighter.submission_wins = submission_wins or None
                fighter.fighting_style = fighting_style
                updated += 1

                if i % 200 == 0:
                    _progress_log("ML Stats", i, total, start)
                    self.session.commit()

            except Exception as e:
                error_msg = f"Erro ao agregar ML stats de {fighter.name}: {str(e)}"
                self.stats["errors"].append(error_msg)
                print(f"  ⚠️  {error_msg}")
                continue

        self.session.commit()
        elapsed = time.time() - start
        print(f"✓ ML stats atualizados para {updated:,} lutadores em {int(elapsed//60)}m{int(elapsed%60):02d}s")

    def recalculate_fighter_attributes(self):
        """
        Recalcula os 6 atributos de jogo (0-100) usando ML stats agregadas.

        Usa as métricas calculadas em update_fighter_ml_stats() mais dados de
        cartel (wins, losses, win_rate) e bônus (KO/sub wins, finish_rate)
        para produzir scores mais precisos que os atributos iniciais do CSV.

        Atributos recalculados:
        - striking: SLpM + precisão + knockdowns + finish_rate + strike_diff
        - grappling: TD avg + sub avg + finish_rate + diferencial de queda
        - defense: str_def + td_def (média ponderada das defesas)
        - stamina: base 65 + experiência + win_rate
        - speed: SLpM + precisão + knockdowns
        - strategy: base 55 + experiência + win_rate
        """
        fighters = (
            self.session.query(Fighter).filter(Fighter.is_real == True).all()
        )
        total = len(fighters)
        print(f"\n🎯 Recalculando atributos para {total:,} lutadores...")
        start = time.time()
        updated = 0

        for i, fighter in enumerate(fighters, 1):
            try:
                wins = fighter.wins or 0
                losses = fighter.losses or 0
                draws = fighter.draws or 0
                total_fights = wins + losses + draws
                win_rate = (wins / total_fights * 100) if total_fights > 0 else 50

                slpm = fighter.slpm or 3
                str_acc = fighter.str_acc or 45
                str_def = fighter.str_def or 50
                sapm = fighter.sapm or 2.5
                td_avg = fighter.td_avg or 1
                td_def = fighter.td_def or 50
                sub_avg = fighter.sub_avg or 0.2
                kd_avg = getattr(fighter, 'kd_avg', None) or 0
                ko_wins = getattr(fighter, 'ko_wins', None) or 0
                sub_wins = getattr(fighter, 'submission_wins', None) or 0

                finish_rate = ((ko_wins + sub_wins) / wins * 100) if wins > 0 else 0
                strike_diff = slpm - sapm  # Diferencial de golpes (positivo = bom)

                # --- Cálculo dos 6 atributos (escala 0-100, valor mínimo garantido) ---

                # Striking: volume (SLpM * 18) + precisão (str_acc * 0.4) + knockdowns (kd_avg * 10)
                # + capacidade de finalizar (finish_rate * 0.25) + diferencial positivo (strike_diff * 3)
                striking = min(100, int(
                    slpm * 18 + str_acc * 0.4 + kd_avg * 10 + finish_rate * 0.25 + max(0, strike_diff) * 3
                ))
                # Grappling: quedas (td_avg * 25) + submissões (sub_avg * 35) + finish_rate * 0.20
                # + eficiência ofensiva de quedas (td_avg - taxa de defesa do oponente)
                grappling = min(100, int(
                    td_avg * 25 + sub_avg * 35 + finish_rate * 0.20 + (td_avg - (1 - td_def / 100)) * 5
                ))
                # Defense: média ponderada de defesa de golpes (70%) e defesa de quedas (60%)
                defense = min(100, int(str_def * 0.7 + td_def * 0.6))
                # Stamina: base 65 + bônus por experiência (+0.8/luta) + bônus por win_rate
                stamina = min(100, int(65 + total_fights * 0.8 + win_rate * 0.25))
                # Speed: volume (SLpM * 16) + precisão (str_acc * 0.4) + knockdowns (kd_avg * 5)
                speed = min(100, int(slpm * 16 + str_acc * 0.4 + kd_avg * 5))
                # Strategy: base 55 + bônus por experiência (+0.6/luta) + bônus por win_rate
                strategy = min(100, int(55 + total_fights * 0.6 + win_rate * 0.30))

                fighter.striking = striking
                fighter.grappling = grappling
                fighter.defense = defense
                fighter.stamina = stamina
                fighter.speed = speed
                fighter.strategy = strategy

                updated += 1

                if i % 500 == 0:
                    _progress_log("Atributos", i, total, start)
                    self.session.commit()

            except Exception as e:
                error_msg = f"Erro ao recalcular atributos de {fighter.name}: {str(e)}"
                self.stats["errors"].append(error_msg)
                print(f"  ⚠️  {error_msg}")
                continue

        self.session.commit()
        elapsed = time.time() - start
        print(f"✓ Atributos recalculados para {updated:,} lutadores em {int(elapsed//60)}m{int(elapsed%60):02d}s")

    def update_event_names(self):
        """
        Atualiza nomes dos eventos usando o campo event_name do fight_details.csv.

        Os eventos são criados inicialmente com nome temporário (ex.: "UFC Event abc12345").
        Este método varre fight_details.csv para extrair o nome real de cada evento
        e atualiza o registro correspondente no banco.

        Fallback: Para eventos que permanecem com nome temporário (sem event_name no CSV),
        constrói um nome a partir dos lutadores da luta principal (fight_order=1).
        """
        print("\n📝 Atualizando nomes dos eventos...")

        temp_name_events = set()

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
                event = self.session.get(Event, event_uuid)
                if event:
                    event.name = name

        self.session.commit()

        # Fallback: para eventos que ainda têm nome temporário, construir a partir das lutas
        from sqlalchemy.orm import joinedload

        for ufcstats_id, event_uuid in self.event_id_map.items():
            event = self.session.get(
                Event,
                event_uuid,
                options=[joinedload(Event.fights).joinedload(Fight.fighter1), joinedload(Event.fights).joinedload(Fight.fighter2)],
            )
            if event and event.name.startswith("UFC Event "):
                main_fight = next(
                    (f for f in event.fights if f.fight_order == 1), None
                )
                if main_fight and main_fight.fighter1 and main_fight.fighter2:
                    event.name = (
                        f"{main_fight.fighter1.name} vs {main_fight.fighter2.name}"
                    )
                    print(f"  📝 Fallback: {ufcstats_id[:8]} -> {event.name}")
                else:
                    temp_name_events.add(event.ufcstats_id or str(event.id)[:8])

        self.session.commit()

        if temp_name_events:
            print(
                f"  ⚠️  {len(temp_name_events)} eventos permanecem com nome temporário (sem lutas principais): "
                f"{', '.join(sorted(temp_name_events))}"
            )

        print(f"✓ Nomes atualizados para {len(event_names)} eventos")

    def update_weight_classes(self):
        """
        Atualiza a categoria de peso (actual_weight_class) de cada lutador.

        Varre o UFC.csv e, para cada lutador, identifica a categoria de peso
        da sua luta mais recente (baseado na data). A luta mais recente é
        considerada a categoria atual do lutador.
        """
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

                # Atualiza categoria de peso se esta luta for mais recente que a anterior.
                # Guarda (weight_class, fight_date) para cada lutador no dicionário.
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
        """
        Imprime estatísticas finais da importação no console.

        Exibe contadores de lutadores, eventos e lutas criados/atualizados,
        além dos primeiros 10 erros encontrados durante o processo.
        """
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
    """
    Função principal de importação do dataset UFC.

    Pipeline de 9 etapas executadas em ordem (cada etapa depende das anteriores):
      1. Importar lutadores (fighter_details.csv) — necessário para foreign keys.
      2. Importar eventos (event_details.csv).
      3. Importar lutas (fight_details.csv) — requer lutadores e eventos mapeados.
      4. Popular vencedores (UFC.csv) — requer lutas já importadas.
      5. Agregar ML stats, KO/Sub wins e fighting_style dos lutadores.
      6. Atualizar nomes reais dos eventos (do fight_details.csv).
      7. Atualizar cartel dos lutadores — requer vencedores já populados.
      8. Atualizar categorias de peso — usa a luta mais recente de cada lutador.
      9. Recalcular atributos de jogo com dados agregados (ML stats + win rate).
    """
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

        # 5. Agregar ML stats, KO/Sub wins e fighting_style dos lutadores
        importer.update_fighter_ml_stats()

        # 6. Atualizar nomes dos eventos
        importer.update_event_names()

        # 7. Atualizar cartel dos lutadores (requer vencedores já populados)
        importer.update_fighter_cartels()

        # 8. Atualizar categorias de peso dos lutadores
        importer.update_weight_classes()

        # 9. Recalcular atributos usando ML stats + KO/sub wins + win rate
        importer.recalculate_fighter_attributes()

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
