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

    # Atributos de luta (0-100)
    striking = Column(Integer, nullable=False)  # Habilidade de striking/trocação
    grappling = Column(Integer, nullable=False)  # Habilidade de grappling/luta agarrada
    defense = Column(Integer, nullable=False)  # Capacidade defensiva
    stamina = Column(Integer, nullable=False)  # Resistência/Cardio
    speed = Column(Integer, nullable=False)  # Velocidade
    strategy = Column(Integer, nullable=False)  # QI de luta/estratégia

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
    age = Column(Integer, nullable=True)
    height_cm = Column(Float, nullable=True)
    reach_cm = Column(Float, nullable=True)
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


class FightSimulation(BaseModel):
    """Simulações de lutas entre lutadores"""

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
