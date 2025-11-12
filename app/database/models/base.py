import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.mutable import MutableDict, MutableList
from sqlalchemy.orm import relationship
from sqlalchemy.types import TIMESTAMP

Base = declarative_base()


class BaseModel(Base):
    __abstract__ = True
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_by = Column(String(150), nullable=False, default="system")
    created_at = Column(
        type_=TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_by = Column(String(150), nullable=False, default="system")
    updated_at = Column(
        type_=TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    deleted_by = Column(String(150), nullable=True)
    deleted_at = Column(type_=TIMESTAMP(timezone=True), nullable=True)

    def to_dict(self):
        return {
            column.name: getattr(self, column.name) for column in self.__table__.columns
        }


class User(BaseModel):
    """Usuários do sistema - podem criar e simular lutas"""

    __tablename__ = "users"

    email = Column(String(150), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    name = Column(String(150), nullable=False)
    role = Column(String(50), nullable=False, default="user")

    # Relacionamentos
    fighters = relationship(
        "Fighter", back_populates="creator", cascade="all, delete-orphan"
    )


class Fighter(BaseModel):
    """Lutadores - podem ser reais ou fictícios"""

    __tablename__ = "fighters"

    # ID do ufcstats.com para lutadores reais
    ufcstats_id = Column(String(50), nullable=True, unique=True, index=True)

    # Informações básicas
    name = Column(String(350), nullable=False, index=True)
    nickname = Column(String(100), nullable=True)
    last_organization_fight = Column(
        String(50), nullable=True
    )  # UFC, Bellator, ONE, etc
    actual_weight_class = Column(
        String(50), nullable=True
    )  # Peso-pena, Peso-médio, etc
    fighting_style = Column(
        String(100), nullable=True
    )  # Striker, Grappler, All-around, etc

    # Dados biográficos do UFC Stats
    date_of_birth = Column(TIMESTAMP(timezone=False), nullable=True)
    stance = Column(String(50), nullable=True)  # Orthodox, Southpaw, Switch
    weight_lbs = Column(Float, nullable=True)
    height_cm = Column(Float, nullable=True)  # Altura em centímetros
    reach_cm = Column(Float, nullable=True)  # Alcance em centímetros

    # Atributos de luta (0-100)
    striking = Column(Integer, nullable=False)  # Habilidade de striking/trocação
    grappling = Column(Integer, nullable=False)  # Habilidade de grappling/luta agarrada
    defense = Column(Integer, nullable=False)  # Capacidade defensiva
    stamina = Column(Integer, nullable=False)  # Resistência/Cardio
    speed = Column(Integer, nullable=False)  # Velocidade
    strategy = Column(Integer, nullable=False)  # QI de luta/estratégia

    # Estatísticas avançadas do UFC Stats
    slpm = Column(Float, nullable=True)  # Significant Strikes Landed per Minute
    str_acc = Column(Float, nullable=True)  # Striking Accuracy %
    sapm = Column(Float, nullable=True)  # Significant Strikes Absorbed per Minute
    str_def = Column(Float, nullable=True)  # Striking Defense %
    td_avg = Column(Float, nullable=True)  # Average Takedowns per 15 min
    td_acc = Column(Float, nullable=True)  # Takedown Accuracy %
    td_def = Column(Float, nullable=True)  # Takedown Defense %
    sub_avg = Column(Float, nullable=True)  # Average Submissions per 15 min

    # Estatísticas reais (deprecated - usar cartel)
    wins = Column(Integer, nullable=True, default=0)
    losses = Column(Integer, nullable=True, default=0)
    draws = Column(Integer, nullable=True, default=0)
    ko_wins = Column(Integer, nullable=True, default=0)
    submission_wins = Column(Integer, nullable=True, default=0)

    # Cartel completo do lutador (lista de lutas)
    cartel = Column(
        MutableList.as_mutable(JSONB), nullable=False, default=list
    )  # Lista com histórico de lutas reais
    # Formato: [{"opponent": "Name", "result": "W/L/D", "method": "KO/Sub/Dec", "round": 1, "date": "2024-01-01", "organization": "UFC"}]

    # Informações adicionais
    bio = Column(Text, nullable=True)
    image_url = Column(String(500), nullable=True)
    is_real = Column(Boolean, default=True, nullable=False)  # Real ou fictício

    # Relação com usuário criador
    creator_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    creator = relationship("User", back_populates="fighters")

    # Relacionamentos com simulações
    fights_as_fighter1 = relationship(
        "FightSimulation",
        foreign_keys="FightSimulation.fighter1_id",
        back_populates="fighter1",
    )
    fights_as_fighter2 = relationship(
        "FightSimulation",
        foreign_keys="FightSimulation.fighter2_id",
        back_populates="fighter2",
    )

    @property
    def age(self) -> int | None:
        """Calcula idade atual do lutador baseado na data de nascimento"""
        if not self.date_of_birth:
            return None
        today = datetime.now(timezone.utc)
        born = self.date_of_birth
        # Se date_of_birth não tem timezone, assume UTC
        if born.tzinfo is None:
            born = born.replace(tzinfo=timezone.utc)
        return (
            today.year - born.year - ((today.month, today.day) < (born.month, born.day))
        )

    @property
    def height_inches(self) -> float | None:
        """Converte altura de cm para polegadas"""
        if not self.height_cm:
            return None
        return round(self.height_cm / 2.54, 2)

    @property
    def reach_inches(self) -> float | None:
        """Converte alcance de cm para polegadas"""
        if not self.reach_cm:
            return None
        return round(self.reach_cm / 2.54, 2)


class Event(BaseModel):
    """Eventos de MMA com múltiplas lutas"""

    __tablename__ = "events"

    # ID do ufcstats.com para eventos reais
    ufcstats_id = Column(String(50), nullable=True, unique=True, index=True)

    # Informações do evento
    name = Column(String(255), nullable=False)  # Ex: "UFC 233"
    date = Column(TIMESTAMP(timezone=True), nullable=False)  # Data do evento
    location = Column(String(255), nullable=True)  # Local do evento
    organization = Column(String(100), nullable=False)  # UFC, Bellator, ONE, etc
    description = Column(Text, nullable=True)  # Descrição do evento
    status = Column(
        String(50), nullable=False, default="scheduled"
    )  # scheduled, completed, cancelled
    poster_url = Column(String(500), nullable=True)  # URL do poster do evento

    # Relacionamentos
    fights = relationship("Fight", back_populates="event", cascade="all, delete-orphan")
    creator_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    creator = relationship("User")


class Fight(BaseModel):
    """Lutas individuais dentro de um evento"""

    __tablename__ = "fights"

    # ID do ufcstats.com para lutas reais
    ufcstats_id = Column(String(50), nullable=True, unique=True, index=True)

    # Relacionamento com evento
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id"), nullable=False)
    event = relationship("Event", back_populates="fights")

    # Lutadores
    fighter1_id = Column(UUID(as_uuid=True), ForeignKey("fighters.id"), nullable=False)
    fighter2_id = Column(UUID(as_uuid=True), ForeignKey("fighters.id"), nullable=False)

    # Ordem da luta no card
    fight_order = Column(Integer, nullable=False)  # 1 = main event, 2 = co-main, etc
    fight_type = Column(
        String(50), nullable=False, default="standard"
    )  # main, co-main, prelim, standard
    weight_class = Column(String(100), nullable=True)  # Categoria da luta
    rounds = Column(Integer, nullable=False, default=3)  # 3 ou 5 rounds
    is_title_fight = Column(Boolean, default=False, nullable=False)

    # Resultado da luta (preenchido após simulação)
    winner_id = Column(
        UUID(as_uuid=True), ForeignKey("fighters.id"), nullable=True
    )  # Null se não simulado ainda
    result_type = Column(
        String(50), nullable=True
    )  # KO, TKO, Submission, Decision, Draw
    finish_round = Column(Integer, nullable=True)  # Round que terminou
    finish_time = Column(String(10), nullable=True)  # Tempo no round (ex: "2:34")
    method_details = Column(
        Text, nullable=True
    )  # Detalhes do método (ex: "Rear Naked Choke")
    match_time_seconds = Column(
        Integer, nullable=True
    )  # Tempo total da luta em segundos
    referee = Column(String(150), nullable=True)  # Nome do árbitro

    # Estatísticas da simulação
    fighter1_probability = Column(Float, nullable=True)
    fighter2_probability = Column(Float, nullable=True)
    simulation_details = Column(
        MutableDict.as_mutable(JSONB), nullable=True, default=dict
    )

    # Estatísticas detalhadas da luta real (Red Corner - fighter1)
    r_kd = Column(Integer, nullable=True)  # Knockdowns
    r_sig_str_landed = Column(Integer, nullable=True)  # Significant strikes landed
    r_sig_str_attempted = Column(
        Integer, nullable=True
    )  # Significant strikes attempted
    r_total_str_landed = Column(Integer, nullable=True)  # Total strikes landed
    r_total_str_attempted = Column(Integer, nullable=True)  # Total strikes attempted
    r_td_landed = Column(Integer, nullable=True)  # Takedowns landed
    r_td_attempted = Column(Integer, nullable=True)  # Takedowns attempted
    r_sub_att = Column(Integer, nullable=True)  # Submission attempts
    r_ctrl_seconds = Column(Integer, nullable=True)  # Control time in seconds

    # Estatísticas detalhadas da luta real (Blue Corner - fighter2)
    b_kd = Column(Integer, nullable=True)
    b_sig_str_landed = Column(Integer, nullable=True)
    b_sig_str_attempted = Column(Integer, nullable=True)
    b_total_str_landed = Column(Integer, nullable=True)
    b_total_str_attempted = Column(Integer, nullable=True)
    b_td_landed = Column(Integer, nullable=True)
    b_td_attempted = Column(Integer, nullable=True)
    b_sub_att = Column(Integer, nullable=True)
    b_ctrl_seconds = Column(Integer, nullable=True)

    # Status da luta
    status = Column(
        String(50), nullable=False, default="scheduled"
    )  # scheduled, simulated, completed, cancelled

    # Relacionamentos com lutadores
    fighter1 = relationship("Fighter", foreign_keys=[fighter1_id])
    fighter2 = relationship("Fighter", foreign_keys=[fighter2_id])
    winner = relationship("Fighter", foreign_keys=[winner_id])


class FightSimulation(BaseModel):
    """Simulações de lutas entre lutadores (simulações avulsas, não vinculadas a eventos)"""

    __tablename__ = "fight_simulations"

    # Lutadores envolvidos
    fighter1_id = Column(UUID(as_uuid=True), ForeignKey("fighters.id"), nullable=False)
    fighter2_id = Column(UUID(as_uuid=True), ForeignKey("fighters.id"), nullable=False)

    # Resultado da simulação
    winner_id = Column(UUID(as_uuid=True), nullable=False)  # ID do vencedor
    result_type = Column(String(50), nullable=False)  # KO, Submission, Decision, Draw
    rounds = Column(Integer, nullable=False, default=3)  # Número de rounds
    finish_round = Column(
        Integer, nullable=True
    )  # Round em que acabou (se não foi decisão)

    # Estatísticas da luta
    fighter1_probability = Column(
        Float, nullable=False
    )  # Probabilidade de vitória do fighter1
    fighter2_probability = Column(
        Float, nullable=False
    )  # Probabilidade de vitória do fighter2

    # Detalhes da simulação
    simulation_details = Column(
        MutableDict.as_mutable(JSONB), nullable=False, default=dict
    )  # JSON com detalhes round a round
    notes = Column(Text, nullable=True)  # Observações sobre a simulação

    # Relacionamentos
    fighter1 = relationship(
        "Fighter", foreign_keys=[fighter1_id], back_populates="fights_as_fighter1"
    )
    fighter2 = relationship(
        "Fighter", foreign_keys=[fighter2_id], back_populates="fights_as_fighter2"
    )
