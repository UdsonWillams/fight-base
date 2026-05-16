"""Serviço para simulação de lutas entre lutadores"""

import random
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from app.core.logger import logger
from app.database.models.base import Fighter, FightSimulation
from app.database.repositories.fight_simulation import FightSimulationRepository
from app.database.repositories.fighter import FighterRepository
from app.exceptions.exceptions import ForbiddenError, NotFoundError
from app.services.ml.prediction_service import ml_prediction_service


@dataclass
class FightSimulationResult:
    """Resultado puro da simulação de luta, sem vínculo com banco de dados."""

    winner_id: UUID
    result_type: str
    finish_round: Optional[int]
    rounds: int
    fighter1_total_points: float
    fighter2_total_points: float
    round_details: list[dict] = field(default_factory=list)


class FightSimulationService:
    """Serviço para gerenciar e executar simulações de lutas"""

    def __init__(
        self,
        fighter_repo: FighterRepository,
        simulation_repo: FightSimulationRepository,
    ):
        self.fighter_repo = fighter_repo
        self.simulation_repo = simulation_repo

    def _calculate_fighter_power(self, fighter: Fighter, aspect: str) -> float:
        """
        Calcula o poder geral de um lutador para um aspecto específico da luta

        Args:
            fighter: Lutador
            aspect: 'striking', 'grappling' ou 'overall'
        """
        if aspect == "striking":
            return fighter.striking * 0.5 + fighter.speed * 0.3 + fighter.defense * 0.2
        elif aspect == "grappling":
            return (
                fighter.grappling * 0.5 + fighter.stamina * 0.3 + fighter.strategy * 0.2
            )
        else:  # overall
            return (
                fighter.striking
                + fighter.grappling
                + fighter.defense
                + fighter.stamina
                + fighter.speed
                + fighter.strategy
            ) / 6

    async def calculate_win_probability(
        self, fighter1: Fighter, fighter2: Fighter
    ) -> tuple[float, float]:
        """
        Calcula a probabilidade de vitória de cada lutador usando modelo ML
        Fallback para método legado se ML não disponível

        Returns:
            (probabilidade_fighter1, probabilidade_fighter2)
        """
        ml_prob = await ml_prediction_service.predict_winner_from_model(
            fighter1, fighter2
        )

        if ml_prob is not None:
            prob1 = ml_prob * 100

            # Ajuste para cross-weight: o modelo foi treinado com lutas da mesma categoria
            w1 = fighter1.weight_lbs or 155
            w2 = fighter2.weight_lbs or 155
            weight_pct = abs(w1 - w2) / max(w1, w2)
            if weight_pct > 0.10:  # diferenca > 10% do peso = categorias diferentes
                if w1 > w2:
                    prob1 = min(98, prob1 + weight_pct * 50)
                else:
                    prob1 = max(2, prob1 - weight_pct * 50)

            prob2 = 100 - prob1
            logger.info(
                f"🤖 Usando predição ML: {fighter1.name} {prob1:.2f}% vs {fighter2.name} {prob2:.2f}%"
            )
            return round(prob1, 2), round(prob2, 2)

        logger.warning(
            "⚠️  ML não disponível, usando cálculo legado com atributos mágicos"
        )

        power1 = self._calculate_fighter_power(fighter1, "overall")
        power2 = self._calculate_fighter_power(fighter2, "overall")

        total_power = power1 + power2
        prob1 = (power1 / total_power) * 100
        prob2 = (power2 / total_power) * 100

        total_fights1 = (
            (fighter1.wins or 0) + (fighter1.losses or 0) + (fighter1.draws or 0)
        )
        total_fights2 = (
            (fighter2.wins or 0) + (fighter2.losses or 0) + (fighter2.draws or 0)
        )

        if fighter1.wins and total_fights1 > 0:
            prob1 += (fighter1.wins / total_fights1) * 5

        if fighter2.wins and total_fights2 > 0:
            prob2 += (fighter2.wins / total_fights2) * 5

        total_prob = prob1 + prob2
        prob1 = (prob1 / total_prob) * 100
        prob2 = (prob2 / total_prob) * 100

        return round(prob1, 2), round(prob2, 2)

    def predict_result_type(
        self, fighter1: Fighter, fighter2: Fighter
    ) -> dict[str, float]:
        """
        Prevê as probabilidades de cada tipo de resultado

        Returns:
            Dict com probabilidades de KO, Submission, Decision
        """
        # Calcula vantagens
        striking1 = self._calculate_fighter_power(fighter1, "striking")
        striking2 = self._calculate_fighter_power(fighter2, "striking")

        grappling1 = self._calculate_fighter_power(fighter1, "grappling")
        grappling2 = self._calculate_fighter_power(fighter2, "grappling")

        # Diferença de striking influencia probabilidade de KO
        striking_diff = abs(striking1 - striking2)
        ko_prob = min(30 + striking_diff * 0.5, 50)  # 30-50%

        # Diferença de grappling influencia probabilidade de finalização
        grappling_diff = abs(grappling1 - grappling2)
        submission_prob = min(20 + grappling_diff * 0.3, 35)  # 20-35%

        # Resto vai para decisão
        decision_prob = 100 - ko_prob - submission_prob

        return {
            "ko": round(ko_prob, 2),
            "submission": round(submission_prob, 2),
            "decision": round(decision_prob, 2),
        }

    def _simulate_round(
        self, fighter1: Fighter, fighter2: Fighter, round_number: int
    ) -> dict:
        """
        Simula um round individual com eventos para AMBOS os lutadores.
        Balanceado para ser divertido: 70% stats + 30% aleatoriedade.
        """
        ROUND_MINUTES = 5

        # --- Cálculo de pontos (scores internos) ---
        striking_offense1 = (fighter1.slpm or 3.0) * ROUND_MINUTES
        striking_defense1 = ((fighter1.str_def or 50) / 100) * 10
        striking_score1 = striking_offense1 + striking_defense1

        striking_offense2 = (fighter2.slpm or 3.0) * ROUND_MINUTES
        striking_defense2 = ((fighter2.str_def or 50) / 100) * 10
        striking_score2 = striking_offense2 + striking_defense2

        grappling_offense1 = ((fighter1.td_avg or 1.0) / 3) * ROUND_MINUTES
        submission_threat1 = ((fighter1.sub_avg or 0.5) / 3) * ROUND_MINUTES * 2
        grappling_defense1 = ((fighter1.td_def or 50) / 100) * 5
        grappling_score1 = grappling_offense1 + submission_threat1 + grappling_defense1

        grappling_offense2 = ((fighter2.td_avg or 1.0) / 3) * ROUND_MINUTES
        submission_threat2 = ((fighter2.sub_avg or 0.5) / 3) * ROUND_MINUTES * 2
        grappling_defense2 = ((fighter2.td_def or 50) / 100) * 5
        grappling_score2 = grappling_offense2 + submission_threat2 + grappling_defense2

        base_points1 = (striking_score1 * 0.6) + (grappling_score1 * 0.4)
        base_points2 = (striking_score2 * 0.6) + (grappling_score2 * 0.4)

        # --- Modificadores físicos (peso, alcance, altura, idade) ---
        f1_w = fighter1.weight_lbs or 155
        f2_w = fighter2.weight_lbs or 155
        f1_r = fighter1.reach_inches or 70
        f2_r = fighter2.reach_inches or 70
        f1_h = fighter1.height_inches or 69
        f2_h = fighter2.height_inches or 69

        # Idade: prime 27-32 ganha bonus, acima de 35 perde
        def _age_factor(dob):
            if not dob:
                return 1.0
            age = (
                datetime.now(timezone.utc) - dob.replace(tzinfo=timezone.utc)
                if dob.tzinfo is None
                else dob
            ).days / 365.25
            if 27 <= age <= 32:
                return 1.05
            if age > 35:
                return max(0.88, 1.0 - (age - 35) * 0.015)
            return 1.0

        # Peso: cada 10lbs de vantagem = +5% (cap 25%)
        weight_diff_abs = abs(f1_w - f2_w)
        weight_bonus = min(weight_diff_abs / 10 * 0.05, 0.25)

        # Alcance: cada 2in = +2% striking
        reach_bonus = abs(f1_r - f2_r) / 2 * 0.02

        # Altura: cada 3in = +1% striking
        height_bonus = abs(f1_h - f2_h) / 3 * 0.01

        # Aplica bonus no mais pesado/mais longo/mais alto
        phys_mult1 = 1.0
        phys_mult2 = 1.0
        if f1_w > f2_w:
            phys_mult1 += weight_bonus
        else:
            phys_mult2 += weight_bonus
        if f1_r > f2_r:
            phys_mult1 += reach_bonus
        else:
            phys_mult2 += reach_bonus
        if f1_h > f2_h:
            phys_mult1 += height_bonus
        else:
            phys_mult2 += height_bonus

        phys_mult1 *= _age_factor(fighter1.date_of_birth)
        phys_mult2 *= _age_factor(fighter2.date_of_birth)

        # Aplica modificadores físicos nos pontos base
        points1 = base_points1 * phys_mult1 * random.uniform(0.75, 1.25)  # nosec B311
        points2 = base_points2 * phys_mult2 * random.uniform(0.75, 1.25)  # nosec B311

        dominant = fighter1.name if points1 > points2 else fighter2.name
        underdog = fighter2.name if dominant == fighter1.name else fighter1.name

        # --- Gerador de eventos para AMBOS os lutadores ---
        events = []
        max_events = random.randint(3, 6)  # nosec B311

        # Diferença significativa indica dominância
        point_diff = abs(points1 - points2)
        if point_diff > 5:
            events.append(f"{dominant} dominou o round")

        # Eventos para lutador1
        td1 = min((fighter1.td_avg or 1.0) / 5, 0.40)
        slpm1 = min((fighter1.slpm or 3.0) / 6, 0.35)
        sub1 = min((fighter1.sub_avg or 0.5) / 3, 0.25)
        td_def2 = min((fighter2.td_def or 50) / 100 * 0.3, 0.30)
        str_def2 = min((fighter2.str_def or 50) / 100 * 0.2, 0.20)

        if random.random() < td1:  # nosec B311
            if random.random() < td_def2:  # nosec B311
                events.append(
                    f"{fighter1.name} tentou o takedown, mas {fighter2.name} defendeu"
                )
            else:
                events.append(
                    f"{fighter1.name} derrubou {fighter2.name} com um takedown"
                )
        if random.random() < slpm1:  # nosec B311
            if random.random() < str_def2:  # nosec B311
                events.append(
                    f"{fighter1.name} avançou com uma combinacao, {fighter2.name} esquivou"
                )
            else:
                events.append(f"{fighter1.name} acertou um direto certeiro no queixo")
        if random.random() < sub1:  # nosec B311
            events.append(f"{fighter1.name} buscou uma finalizacao no chao")

        # Eventos para lutador2
        td2 = min((fighter2.td_avg or 1.0) / 5, 0.40)
        slpm2 = min((fighter2.slpm or 3.0) / 6, 0.35)
        sub2 = min((fighter2.sub_avg or 0.5) / 3, 0.25)
        td_def1 = min((fighter1.td_def or 50) / 100 * 0.3, 0.30)
        str_def1 = min((fighter1.str_def or 50) / 100 * 0.2, 0.20)

        if random.random() < td2:  # nosec B311
            if random.random() < td_def1:  # nosec B311
                events.append(
                    f"{fighter2.name} tentou o takedown, mas {fighter1.name} defendeu"
                )
            else:
                events.append(
                    f"{fighter2.name} derrubou {fighter1.name} com um takedown"
                )
        if random.random() < slpm2:  # nosec B311
            if random.random() < str_def1:  # nosec B311
                events.append(
                    f"{fighter2.name} avançou com uma combinacao, {fighter1.name} esquivou"
                )
            else:
                events.append(f"{fighter2.name} acertou um uppercut devastador")
        if random.random() < sub2:  # nosec B311
            events.append(f"{fighter2.name} buscou uma finalizacao no chao")

        # Eventos neutros (20% chance cada)
        neutrals = [
            "Trocação equilibrada no centro do octogono",
            "Clinch na grade, ambos lutando por posicao",
            f"{dominant} controlou o centro do octogono",
            f"{underdog} tentou manter a distancia com jabs",
            "Round ritmado com muita trocação de baixa potencia",
        ]
        if random.random() < 0.20:  # nosec B311
            events.append(random.choice(neutrals))  # nosec B311

        # Eventos de vantagem fisica (peso, alcance, altura)
        if phys_mult1 > 1.05 and random.random() < 0.30:  # nosec B311
            if (f1_r - f2_r) > 2:
                events.append(
                    f"{fighter1.name} manteve {fighter2.name} na ponta do jab com seu alcance superior"
                )
            elif (f1_w - f2_w) > 15:
                events.append(f"{fighter1.name} mostrou poder superior no clinch")
            else:
                events.append(
                    f"{fighter1.name} usou sua vantagem fisica para controlar"
                )
        if phys_mult2 > 1.05 and random.random() < 0.30:  # nosec B311
            if (f2_r - f1_r) > 2:
                events.append(
                    f"{fighter2.name} manteve {fighter1.name} na ponta do jab com seu alcance superior"
                )
            elif (f2_w - f1_w) > 15:
                events.append(f"{fighter2.name} mostrou poder superior no clinch")
            else:
                events.append(
                    f"{fighter2.name} usou sua vantagem fisica para controlar"
                )

        if fighter1.date_of_birth and fighter2.date_of_birth:
            f1_age = (
                datetime.now(timezone.utc)
                - fighter1.date_of_birth.replace(tzinfo=timezone.utc)
                if fighter1.date_of_birth.tzinfo is None
                else fighter1.date_of_birth
            ).days / 365.25
            f2_age = (
                datetime.now(timezone.utc)
                - fighter2.date_of_birth.replace(tzinfo=timezone.utc)
                if fighter2.date_of_birth.tzinfo is None
                else fighter2.date_of_birth
            ).days / 365.25
            if f1_age > 38 and random.random() < 0.15:  # nosec B311
                events.append(
                    f"{fighter1.name} pareceu cansado, idade cobrando seu preco"
                )
            if f2_age > 38 and random.random() < 0.15:  # nosec B311
                events.append(
                    f"{fighter2.name} pareceu cansado, idade cobrando seu preco"
                )

        # Limita a max_events
        if len(events) > max_events:
            random.shuffle(events)  # nosec B311
            events = events[:max_events]

        # Reordena para que "dominou" fique primeiro se existir
        events.sort(key=lambda e: (0 if "dominou" in e else 1))

        return {
            "round_number": round_number,
            "fighter1_points": round(points1, 2),
            "fighter2_points": round(points2, 2),
            "dominant_fighter": dominant,
            "events": events,
        }

    def _run_fight_simulation(
        self, fighter1: Fighter, fighter2: Fighter, rounds: int
    ) -> FightSimulationResult:
        """
        Método core de simulação: determina resultado, simula rounds e escolhe vencedor.

        Regras:
          - KO/Submission: vencedor = dominante do último round (o round do finish)
          - Decision: vencedor = maior pontuação total acumulada
          - Empate nos pontos totais em Decision: sorteio aleatório entre os dois
        """
        fighter1_id = fighter1.id
        fighter2_id = fighter2.id

        result_types = self.predict_result_type(fighter1, fighter2)

        rand = random.random() * 100  # nosec B311
        if rand < result_types["ko"]:
            result_type = "KO"
            finish_round = (
                random.randint(1, rounds - 1) if rounds > 1 else 1  # nosec B311
            )
        elif rand < result_types["ko"] + result_types["submission"]:
            result_type = "Submission"
            finish_round = (
                random.randint(1, rounds - 1) if rounds > 1 else 1  # nosec B311
            )
        else:
            result_type = "Decision"
            finish_round = None

        rounds_to_simulate = finish_round if finish_round else rounds

        round_details = []
        f1_total = 0.0
        f2_total = 0.0

        for round_num in range(1, rounds_to_simulate + 1):
            round_result = self._simulate_round(fighter1, fighter2, round_num)
            round_details.append(round_result)
            f1_total += round_result["fighter1_points"]
            f2_total += round_result["fighter2_points"]

        if result_type in ("KO", "Submission"):
            last_round = round_details[-1]
            winner_id = (
                fighter1_id
                if last_round["dominant_fighter"] == fighter1.name
                else fighter2_id
            )
        elif f1_total > f2_total:
            winner_id = fighter1_id
        elif f2_total > f1_total:
            winner_id = fighter2_id
        else:
            winner_id = random.choice([fighter1_id, fighter2_id])  # nosec B311

        return FightSimulationResult(
            winner_id=winner_id,
            result_type=result_type,
            finish_round=finish_round,
            rounds=rounds,
            fighter1_total_points=f1_total,
            fighter2_total_points=f2_total,
            round_details=round_details,
        )

    async def simulate_fight(
        self,
        fighter1_id: UUID,
        fighter2_id: UUID,
        rounds: int = 3,
        notes: Optional[str] = None,
        created_by: str = "system",
    ) -> FightSimulation:
        """
        Executa uma simulação completa de luta

        Args:
            fighter1_id: ID do primeiro lutador
            fighter2_id: ID do segundo lutador
            rounds: Número de rounds (1-5)
            notes: Observações sobre a simulação
            created_by: Quem criou a simulação

        Returns:
            FightSimulation com o resultado
        """
        fighter1 = await self.fighter_repo.get_by_id(fighter1_id)
        fighter2 = await self.fighter_repo.get_by_id(fighter2_id)

        if not fighter1:
            raise NotFoundError("Fighter 1 not found")
        if not fighter2:
            raise NotFoundError("Fighter 2 not found")

        if fighter1_id == fighter2_id:
            raise ForbiddenError("Cannot simulate fight between same fighter")

        prob1, prob2 = await self.calculate_win_probability(fighter1, fighter2)

        result = self._run_fight_simulation(fighter1, fighter2, rounds)

        simulation = FightSimulation(
            fighter1_id=fighter1_id,
            fighter2_id=fighter2_id,
            winner_id=result.winner_id,
            result_type=result.result_type,
            rounds=rounds,
            finish_round=result.finish_round,
            fighter1_probability=prob1,
            fighter2_probability=prob2,
            simulation_details={
                "rounds": result.round_details,
                "total_points": {
                    "fighter1": round(result.fighter1_total_points, 2),
                    "fighter2": round(result.fighter2_total_points, 2),
                },
            },
            notes=notes,
            created_by=created_by,
        )

        return await self.simulation_repo.create(simulation)

    async def predict_fight(self, fighter1_id: UUID, fighter2_id: UUID) -> dict:
        """
        Faz uma previsão de luta sem executar a simulação

        Returns:
            Dict com análise e probabilidades
        """
        # Busca os lutadores
        fighter1 = await self.fighter_repo.get_by_id(fighter1_id)
        fighter2 = await self.fighter_repo.get_by_id(fighter2_id)

        if not fighter1:
            raise NotFoundError("Fighter 1 not found")
        if not fighter2:
            raise NotFoundError("Fighter 2 not found")

        # Calcula probabilidades
        prob1, prob2 = await self.calculate_win_probability(fighter1, fighter2)
        result_probs = self.predict_result_type(fighter1, fighter2)

        # Análise de vantagens
        striking1 = self._calculate_fighter_power(fighter1, "striking")
        striking2 = self._calculate_fighter_power(fighter2, "striking")

        grappling1 = self._calculate_fighter_power(fighter1, "grappling")
        grappling2 = self._calculate_fighter_power(fighter2, "grappling")

        striking_advantage = fighter1.name if striking1 > striking2 else fighter2.name
        grappling_advantage = (
            fighter1.name if grappling1 > grappling2 else fighter2.name
        )
        overall_advantage = fighter1.name if prob1 > prob2 else fighter2.name

        # Gera análise textual
        analysis_parts = []

        if prob1 > 60 or prob2 > 60:
            favorite = fighter1.name if prob1 > prob2 else fighter2.name
            analysis_parts.append(f"{favorite} é o claro favorito nesta luta.")
        else:
            analysis_parts.append(
                "Esta luta está equilibrada e pode ir para qualquer lado."
            )

        if abs(striking1 - striking2) > 15:
            analysis_parts.append(
                f"{striking_advantage} tem vantagem significativa no striking."
            )

        if abs(grappling1 - grappling2) > 15:
            analysis_parts.append(
                f"{grappling_advantage} tem vantagem significativa no grappling."
            )

        # Fatores chave
        key_factors = []

        if fighter1.stamina > 80 or fighter2.stamina > 80:
            high_stamina_fighter = (
                fighter1.name if fighter1.stamina > fighter2.stamina else fighter2.name
            )
            key_factors.append(f"Cardio de {high_stamina_fighter} pode ser decisivo")

        if fighter1.strategy > 85 or fighter2.strategy > 85:
            smart_fighter = (
                fighter1.name
                if fighter1.strategy > fighter2.strategy
                else fighter2.name
            )
            key_factors.append(f"QI de luta de {smart_fighter} pode fazer a diferença")

        return {
            "fighter1_id": str(fighter1_id),
            "fighter2_id": str(fighter2_id),
            "fighter1_name": fighter1.name,
            "fighter2_name": fighter2.name,
            "fighter1_win_probability": prob1,
            "fighter2_win_probability": prob2,
            "draw_probability": 0.0,  # Desenhos são raros em MMA
            "ko_probability": result_probs["ko"],
            "submission_probability": result_probs["submission"],
            "decision_probability": result_probs["decision"],
            "striking_advantage": striking_advantage,
            "grappling_advantage": grappling_advantage,
            "overall_advantage": overall_advantage,
            "analysis": " ".join(analysis_parts),
            "key_factors": key_factors,
        }

    async def compare_fighters(self, fighter1_id: UUID, fighter2_id: UUID) -> dict:
        """
        Compara dois lutadores em detalhes

        Returns:
            Dict com comparação detalhada
        """
        # Busca os lutadores
        fighter1 = await self.fighter_repo.get_by_id(fighter1_id)
        fighter2 = await self.fighter_repo.get_by_id(fighter2_id)

        if not fighter1:
            raise NotFoundError("Fighter 1 not found")
        if not fighter2:
            raise NotFoundError("Fighter 2 not found")

        # Compara cada atributo
        comparisons = {
            "striking": {
                "fighter1": fighter1.striking,
                "fighter2": fighter2.striking,
                "advantage": fighter1.name
                if fighter1.striking > fighter2.striking
                else fighter2.name,
                "diff": abs(fighter1.striking - fighter2.striking),
            },
            "grappling": {
                "fighter1": fighter1.grappling,
                "fighter2": fighter2.grappling,
                "advantage": fighter1.name
                if fighter1.grappling > fighter2.grappling
                else fighter2.name,
                "diff": abs(fighter1.grappling - fighter2.grappling),
            },
            "defense": {
                "fighter1": fighter1.defense,
                "fighter2": fighter2.defense,
                "advantage": fighter1.name
                if fighter1.defense > fighter2.defense
                else fighter2.name,
                "diff": abs(fighter1.defense - fighter2.defense),
            },
            "stamina": {
                "fighter1": fighter1.stamina,
                "fighter2": fighter2.stamina,
                "advantage": fighter1.name
                if fighter1.stamina > fighter2.stamina
                else fighter2.name,
                "diff": abs(fighter1.stamina - fighter2.stamina),
            },
            "speed": {
                "fighter1": fighter1.speed,
                "fighter2": fighter2.speed,
                "advantage": fighter1.name
                if fighter1.speed > fighter2.speed
                else fighter2.name,
                "diff": abs(fighter1.speed - fighter2.speed),
            },
            "strategy": {
                "fighter1": fighter1.strategy,
                "fighter2": fighter2.strategy,
                "advantage": fighter1.name
                if fighter1.strategy > fighter2.strategy
                else fighter2.name,
                "diff": abs(fighter1.strategy - fighter2.strategy),
            },
        }

        # Calcula overall
        overall1 = self._calculate_fighter_power(fighter1, "overall")
        overall2 = self._calculate_fighter_power(fighter2, "overall")

        comparisons["overall"] = {
            "fighter1": round(overall1, 2),
            "fighter2": round(overall2, 2),
            "advantage": fighter1.name if overall1 > overall2 else fighter2.name,
            "diff": round(abs(overall1 - overall2), 2),
        }

        return {
            "fighter1": {
                "id": str(fighter1.id),
                "name": fighter1.name,
                "record": f"{fighter1.wins}-{fighter1.losses}-{fighter1.draws}",
            },
            "fighter2": {
                "id": str(fighter2.id),
                "name": fighter2.name,
                "record": f"{fighter2.wins}-{fighter2.losses}-{fighter2.draws}",
            },
            "comparisons": comparisons,
        }

    async def get_simulation_with_details(self, simulation: FightSimulation) -> dict:
        """
        Retorna uma simulação com todos os detalhes formatados incluindo nomes dos lutadores.
        """
        fighter1 = await self.fighter_repo.get_by_id(simulation.fighter1_id)
        fighter2 = await self.fighter_repo.get_by_id(simulation.fighter2_id)
        winner = fighter1 if simulation.winner_id == fighter1.id else fighter2

        return {
            "id": str(simulation.id),
            "fighter1_id": str(simulation.fighter1_id),
            "fighter2_id": str(simulation.fighter2_id),
            "fighter1_name": fighter1.name,
            "fighter2_name": fighter2.name,
            "winner_id": str(simulation.winner_id),
            "winner_name": winner.name,
            "result_type": simulation.result_type,
            "rounds": simulation.rounds,
            "finish_round": simulation.finish_round,
            "fighter1_probability": simulation.fighter1_probability,
            "fighter2_probability": simulation.fighter2_probability,
            "simulation_details": simulation.simulation_details,
            "notes": simulation.notes,
            "created_at": simulation.created_at.isoformat(),
        }

    async def get_fighter_history(
        self, fighter_id: UUID, limit: int = 20, offset: int = 0
    ) -> dict:
        """
        Retorna o histórico de simulações de um lutador com estatísticas.
        """
        history = await self.simulation_repo.get_fighter_history(
            fighter_id=fighter_id, limit=limit, offset=offset
        )
        stats = await self.simulation_repo.get_fighter_stats(fighter_id)
        fighter = await self.fighter_repo.get_by_id(fighter_id)

        fights = []
        for sim in history:
            f1 = await self.fighter_repo.get_by_id(sim.fighter1_id)
            f2 = await self.fighter_repo.get_by_id(sim.fighter2_id)
            winner = f1 if sim.winner_id == f1.id else f2

            fights.append(
                {
                    "id": str(sim.id),
                    "fighter1_name": f1.name,
                    "fighter2_name": f2.name,
                    "winner_name": winner.name,
                    "result_type": sim.result_type,
                    "rounds": sim.rounds,
                    "finish_round": sim.finish_round,
                    "created_at": sim.created_at.isoformat(),
                }
            )

        return {
            "fighter_id": str(fighter_id),
            "fighter_name": fighter.name,
            "statistics": stats,
            "recent_fights": fights,
            "pagination": {"limit": limit, "offset": offset, "total": len(fights)},
        }

    async def get_matchup_history_formatted(
        self, fighter1_id: UUID, fighter2_id: UUID
    ) -> list[dict]:
        """
        Retorna o histórico de confrontos diretos entre dois lutadores formatado.
        """
        history = await self.simulation_repo.get_matchup_history(
            fighter1_id, fighter2_id
        )

        results = []
        for sim in history:
            f1 = await self.fighter_repo.get_by_id(sim.fighter1_id)
            f2 = await self.fighter_repo.get_by_id(sim.fighter2_id)
            winner = f1 if sim.winner_id == f1.id else f2

            results.append(
                {
                    "id": str(sim.id),
                    "fighter1_name": f1.name,
                    "fighter2_name": f2.name,
                    "winner_name": winner.name,
                    "result_type": sim.result_type,
                    "rounds": sim.rounds,
                    "finish_round": sim.finish_round,
                    "fighter1_probability": sim.fighter1_probability,
                    "fighter2_probability": sim.fighter2_probability,
                    "created_at": sim.created_at.isoformat(),
                }
            )

        return results

    async def get_recent_simulations_formatted(self, limit: int = 50) -> list[dict]:
        """
        Retorna as simulações recentes formatadas com nomes dos lutadores.
        """
        simulations = await self.simulation_repo.get_recent_simulations(limit)

        results = []
        for sim in simulations:
            f1 = await self.fighter_repo.get_by_id(sim.fighter1_id)
            f2 = await self.fighter_repo.get_by_id(sim.fighter2_id)
            winner = f1 if sim.winner_id == f1.id else f2

            results.append(
                {
                    "id": str(sim.id),
                    "fighter1_name": f1.name,
                    "fighter2_name": f2.name,
                    "winner_name": winner.name,
                    "result_type": sim.result_type,
                    "rounds": sim.rounds,
                    "finish_round": sim.finish_round,
                    "created_at": sim.created_at.isoformat(),
                }
            )

        return results

    async def get_simulation_stats(self) -> dict:
        """
        Retorna estatísticas gerais sobre simulações.

        Returns:
            Dict com total de simulações
        """
        total = await self.simulation_repo.get_total_count()
        return {
            "total_simulations": total,
        }
