"""Serviço para simulação de lutas entre lutadores"""

import random
from typing import Optional
from uuid import UUID

from app.database.models.base import Fighter, FightSimulation
from app.database.repositories.fight_simulation import FightSimulationRepository
from app.database.repositories.fighter import FighterRepository
from app.exceptions.exceptions import BusinessRuleViolation, NotFound


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
            # Striking considera: striking, speed, defense
            return fighter.striking * 0.5 + fighter.speed * 0.3 + fighter.defense * 0.2
        elif aspect == "grappling":
            # Grappling considera: grappling, stamina, strategy
            return (
                fighter.grappling * 0.5 + fighter.stamina * 0.3 + fighter.strategy * 0.2
            )
        else:  # overall
            # Overall é a média de todos os atributos
            return (
                fighter.striking
                + fighter.grappling
                + fighter.defense
                + fighter.stamina
                + fighter.speed
                + fighter.strategy
            ) / 6

    def calculate_win_probability(
        self, fighter1: Fighter, fighter2: Fighter
    ) -> tuple[float, float]:
        """
        Calcula a probabilidade de vitória de cada lutador

        Returns:
            (probabilidade_fighter1, probabilidade_fighter2)
        """
        # Calcula poder geral de cada lutador
        power1 = self._calculate_fighter_power(fighter1, "overall")
        power2 = self._calculate_fighter_power(fighter2, "overall")

        # Calcula diferença de poder
        total_power = power1 + power2

        # Probabilidade base
        prob1 = (power1 / total_power) * 100
        prob2 = (power2 / total_power) * 100

        # Ajusta com base no histórico (se existir)
        if fighter1.wins and fighter1.losses:
            fighter1_record_bonus = (
                fighter1.wins / (fighter1.wins + fighter1.losses)
            ) * 5
            prob1 += fighter1_record_bonus

        if fighter2.wins and fighter2.losses:
            fighter2_record_bonus = (
                fighter2.wins / (fighter2.wins + fighter2.losses)
            ) * 5
            prob2 += fighter2_record_bonus

        # Normaliza para somar 100%
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
        """Simula um round individual"""
        # Calcula pontos para o round
        striking1 = self._calculate_fighter_power(fighter1, "striking")
        striking2 = self._calculate_fighter_power(fighter2, "striking")

        grappling1 = self._calculate_fighter_power(fighter1, "grappling")
        grappling2 = self._calculate_fighter_power(fighter2, "grappling")

        # Adiciona aleatoriedade (10-30% de variação)
        randomness = random.uniform(0.9, 1.1)  # nosec B311

        points1 = (striking1 + grappling1) * randomness
        points2 = (striking2 + grappling2) * randomness

        # Determina dominância
        dominant = fighter1.name if points1 > points2 else fighter2.name

        # Gera eventos do round
        events = []

        if abs(points1 - points2) > 20:
            events.append(f"{dominant} dominou o round")

        if random.random() < 0.3:  # nosec B311 - 30% chance de evento especial
            event_type = random.choice(["takedown", "strike", "submission_attempt"])  # nosec B311
            if event_type == "takedown":
                events.append(f"{dominant} conseguiu um takedown")
            elif event_type == "strike":
                events.append(f"{dominant} acertou um golpe significativo")
            else:
                events.append(f"{dominant} tentou uma finalização")

        return {
            "round_number": round_number,
            "fighter1_points": round(points1, 2),
            "fighter2_points": round(points2, 2),
            "dominant_fighter": dominant,
            "events": events,
        }

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
        # Busca os lutadores
        fighter1 = await self.fighter_repo.get_by_id(fighter1_id)
        fighter2 = await self.fighter_repo.get_by_id(fighter2_id)

        if not fighter1:
            raise NotFound("Fighter 1 not found")
        if not fighter2:
            raise NotFound("Fighter 2 not found")

        if fighter1_id == fighter2_id:
            raise BusinessRuleViolation("Cannot simulate fight between same fighter")

        # Calcula probabilidades
        prob1, prob2 = self.calculate_win_probability(fighter1, fighter2)

        # Simula rounds
        round_details = []
        fighter1_total_points = 0
        fighter2_total_points = 0

        for round_num in range(1, rounds + 1):
            round_result = self._simulate_round(fighter1, fighter2, round_num)
            round_details.append(round_result)
            fighter1_total_points += round_result["fighter1_points"]
            fighter2_total_points += round_result["fighter2_points"]

        # Determina o vencedor com base nos pontos totais
        winner_id = (
            fighter1_id
            if fighter1_total_points > fighter2_total_points
            else fighter2_id
        )

        # Determina o tipo de resultado
        result_types = self.predict_result_type(fighter1, fighter2)

        # Seleciona tipo baseado nas probabilidades
        rand = random.random() * 100  # nosec B311
        if rand < result_types["ko"]:
            result_type = "KO"
            finish_round = random.randint(1, rounds)  # nosec B311
        elif rand < result_types["ko"] + result_types["submission"]:
            result_type = "Submission"
            finish_round = random.randint(1, rounds)  # nosec B311
        else:
            result_type = "Decision"
            finish_round = None

        # Cria a simulação
        simulation = FightSimulation(
            fighter1_id=fighter1_id,
            fighter2_id=fighter2_id,
            winner_id=winner_id,
            result_type=result_type,
            rounds=rounds,
            finish_round=finish_round,
            fighter1_probability=prob1,
            fighter2_probability=prob2,
            simulation_details={
                "rounds": round_details,
                "total_points": {
                    "fighter1": round(fighter1_total_points, 2),
                    "fighter2": round(fighter2_total_points, 2),
                },
            },
            notes=notes,
            created_by=created_by,
        )

        # Salva no banco
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
            raise NotFound("Fighter 1 not found")
        if not fighter2:
            raise NotFound("Fighter 2 not found")

        # Calcula probabilidades
        prob1, prob2 = self.calculate_win_probability(fighter1, fighter2)
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
            raise NotFound("Fighter 1 not found")
        if not fighter2:
            raise NotFound("Fighter 2 not found")

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
