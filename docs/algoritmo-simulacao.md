# 🧠 Algoritmo de Simulação - Detalhes Técnicos

## 📊 Visão Geral

O algoritmo de simulação do FightBase é baseado em estatísticas e probabilidades, combinando atributos dos lutadores com aleatoriedade controlada para gerar resultados realistas.

## 🎯 Componentes do Algoritmo

### 1. Cálculo de Poder (Power Calculation)

#### Striking Power

```python
striking_power = (striking × 0.5) + (speed × 0.3) + (defense × 0.2)
```

**Justificativa:**

- **Striking (50%)**: O atributo principal para trocação
- **Speed (30%)**: Velocidade ajuda a conectar golpes
- **Defense (20%)**: Defesa reduz efetividade do oponente

#### Grappling Power

```python
grappling_power = (grappling × 0.5) + (stamina × 0.3) + (strategy × 0.2)
```

**Justificativa:**

- **Grappling (50%)**: Técnica de luta agarrada/chão
- **Stamina (30%)**: Crucial para manter pressão
- **Strategy (20%)**: Conhecimento tático é essencial

#### Overall Power

```python
overall_power = (striking + grappling + defense + stamina + speed + strategy) / 6
```

**Justificativa:**

- Média simples de todos os atributos
- Representa a completude do lutador

### 2. Cálculo de Probabilidades

```python
def calculate_win_probability(fighter1, fighter2):
    # Poder base
    power1 = overall_power(fighter1)
    power2 = overall_power(fighter2)

    # Probabilidade base (percentual do poder total)
    total_power = power1 + power2
    prob1 = (power1 / total_power) * 100
    prob2 = (power2 / total_power) * 100

    # Ajuste com histórico (se disponível)
    if fighter1.wins and fighter1.losses:
        record_bonus1 = (fighter1.wins / (fighter1.wins + fighter1.losses)) * 5
        prob1 += record_bonus1

    if fighter2.wins and fighter2.losses:
        record_bonus2 = (fighter2.wins / (fighter2.wins + fighter2.losses)) * 5
        prob2 += record_bonus2

    # Normalização (garantir que some 100%)
    total_prob = prob1 + prob2
    prob1 = (prob1 / total_prob) * 100
    prob2 = (prob2 / total_prob) * 100

    return prob1, prob2
```

**Características:**

- Máximo de 5% de bônus por cartel
- Sempre normalizado para 100%
- Considera histórico real se disponível

### 3. Previsão de Tipo de Resultado

```python
def predict_result_type(fighter1, fighter2):
    # Cálculo de vantagens
    striking_diff = abs(striking_power(fighter1) - striking_power(fighter2))
    grappling_diff = abs(grappling_power(fighter1) - grappling_power(fighter2))

    # KO: Base 30% + diferença de striking
    ko_probability = min(30 + (striking_diff * 0.5), 50)

    # Submission: Base 20% + diferença de grappling
    submission_probability = min(20 + (grappling_diff * 0.3), 35)

    # Decision: O que sobrar
    decision_probability = 100 - ko_probability - submission_probability

    return {
        "ko": ko_probability,
        "submission": submission_probability,
        "decision": decision_probability
    }
```

**Limites:**

- KO: 30% mínimo, 50% máximo
- Submission: 20% mínimo, 35% máximo
- Decision: Flexível (15-50%)

### 4. Simulação de Round

```python
def simulate_round(fighter1, fighter2, round_number):
    # Calcular pontos base
    striking1 = striking_power(fighter1)
    striking2 = striking_power(fighter2)
    grappling1 = grappling_power(fighter1)
    grappling2 = grappling_power(fighter2)

    # Adicionar aleatoriedade (10-30%)
    randomness = random.uniform(0.9, 1.1)

    # Pontos do round
    points1 = (striking1 + grappling1) * randomness
    points2 = (striking2 + grappling2) * randomness

    # Determinar dominância
    dominant = fighter1 if points1 > points2 else fighter2

    # Gerar eventos (30% chance)
    events = []
    if random.random() < 0.3:
        event_type = random.choice(['takedown', 'strike', 'submission_attempt'])
        events.append(generate_event(dominant, event_type))

    # Adicionar evento de dominância se diferença significativa
    if abs(points1 - points2) > 20:
        events.append(f"{dominant.name} dominou o round")

    return {
        "round_number": round_number,
        "fighter1_points": points1,
        "fighter2_points": points2,
        "dominant_fighter": dominant.name,
        "events": events
    }
```

**Características:**

- Aleatoriedade de ±10%
- Eventos especiais aleatórios
- Narrativa baseada em dominância

### 5. Execução da Simulação Completa

```python
async def simulate_fight(fighter1_id, fighter2_id, rounds=3):
    # 1. Buscar lutadores
    fighter1 = await get_fighter(fighter1_id)
    fighter2 = await get_fighter(fighter2_id)

    # 2. Calcular probabilidades
    prob1, prob2 = calculate_win_probability(fighter1, fighter2)

    # 3. Simular cada round
    round_details = []
    total_points1 = 0
    total_points2 = 0

    for round_num in range(1, rounds + 1):
        round_result = simulate_round(fighter1, fighter2, round_num)
        round_details.append(round_result)
        total_points1 += round_result["fighter1_points"]
        total_points2 += round_result["fighter2_points"]

    # 4. Determinar vencedor (por pontos)
    winner = fighter1 if total_points1 > total_points2 else fighter2

    # 5. Selecionar tipo de resultado
    result_probs = predict_result_type(fighter1, fighter2)
    rand = random.random() * 100

    if rand < result_probs["ko"]:
        result_type = "KO"
        finish_round = random.randint(1, rounds)
    elif rand < result_probs["ko"] + result_probs["submission"]:
        result_type = "Submission"
        finish_round = random.randint(1, rounds)
    else:
        result_type = "Decision"
        finish_round = None

    # 6. Criar e salvar simulação
    simulation = FightSimulation(
        fighter1_id=fighter1_id,
        fighter2_id=fighter2_id,
        winner_id=winner.id,
        result_type=result_type,
        rounds=rounds,
        finish_round=finish_round,
        fighter1_probability=prob1,
        fighter2_probability=prob2,
        simulation_details={
            "rounds": round_details,
            "total_points": {
                "fighter1": total_points1,
                "fighter2": total_points2
            }
        }
    )

    return await save_simulation(simulation)
```

## 📈 Análise de Probabilidades

### Cenários de Diferença de Atributos

| Diferença    | Probabilidade Típica | Interpretação          |
| ------------ | -------------------- | ---------------------- |
| 0-5 pontos   | 50-55% vs 45-50%     | Luta muito equilibrada |
| 5-10 pontos  | 55-60% vs 40-45%     | Leve favorito          |
| 10-15 pontos | 60-65% vs 35-40%     | Favorito claro         |
| 15-20 pontos | 65-70% vs 30-35%     | Grande favorito        |
| 20+ pontos   | 70-80% vs 20-30%     | Dominação esperada     |

### Distribuição de Tipos de Resultado

#### Striker vs Striker

- KO: 40-50%
- Submission: 15-20%
- Decision: 35-40%

#### Grappler vs Grappler

- KO: 20-25%
- Submission: 35-40%
- Decision: 40-45%

#### Striker vs Grappler (Equilibrado)

- KO: 30-35%
- Submission: 30-35%
- Decision: 30-40%

## 🎲 Aleatoriedade e Realismo

### Fatores Aleatórios

1. **Variação de Performance (±10%)**

   - Simula dias bons/ruins
   - Mantém realismo

2. **Eventos Especiais (30% chance)**

   - Takedowns
   - Golpes significativos
   - Tentativas de finalização

3. **Seleção de Resultado**
   - Baseado em probabilidades calculadas
   - Permite "upsets" realistas

### Garantindo Consistência

```python
# Seed para reproduzibilidade (opcional)
random.seed(simulation_id)

# Limites para evitar extremos
probability = max(10, min(90, calculated_probability))

# Normalização constante
total = sum(probabilities)
normalized = [p / total * 100 for p in probabilities]
```

## 🔬 Validação do Algoritmo

### Testes de Sanidade

1. **Somatório de Probabilidades**

   ```python
   assert prob1 + prob2 == 100.0
   ```

2. **Limites de Atributos**

   ```python
   assert 0 <= attribute <= 100
   ```

3. **Tipos de Resultado**

   ```python
   assert result_type in ["KO", "Submission", "Decision"]
   ```

4. **Rounds Válidos**
   ```python
   assert 1 <= rounds <= 5
   assert finish_round is None or finish_round <= rounds
   ```

## 📊 Melhorias Futuras

### Machine Learning (✅ Implementado)

O FightBase já conta com modelos de ML treinados com dados reais do UFC:

- Modelo: `models/mma_model_v2.joblib`
- Serviço: `app/services/ml/prediction_service.py`
- Carregamento automático no startup da API

```python
# Treinar modelo atualizado com dados do banco
python scripts/train_model_v2_db.py

# Treinar com dados locais
python scripts/train_model_local.py
```

O modelo complementa o algoritmo baseado em regras, fornecendo uma camada adicional de inteligência nas previsões.

### Fatores Adicionais (alguns já implementados via modelo ML)

1. **Altitude/Localização**
   - Ajustar stamina baseado em altitude
2. **Tempo desde última luta**
   - Penalizar lutadores muito ativos
3. **Lesões**
   - Reduzir temporariamente atributos
4. **Camp/Preparação**

   - Bônus temporário em atributos

5. **Matchup específico**
   - Bonificação por estilo favorável

### Análise Avançada

```python
# Heat map de probabilidades
def generate_probability_heatmap(fighter, opponents):
    results = []
    for opponent in opponents:
        prob = calculate_win_probability(fighter, opponent)
        results.append({
            "opponent": opponent.name,
            "probability": prob[0]
        })
    return results

# Monte Carlo
def monte_carlo_simulation(fighter1, fighter2, n=1000):
    results = {"fighter1": 0, "fighter2": 0}
    for _ in range(n):
        winner = simulate_fight(fighter1, fighter2).winner_id
        if winner == fighter1.id:
            results["fighter1"] += 1
        else:
            results["fighter2"] += 1

    return {
        "fighter1_win_rate": results["fighter1"] / n * 100,
        "fighter2_win_rate": results["fighter2"] / n * 100
    }
```

## 🎯 Considerações de Design

### Por que não usar IA desde o início?

1. **Transparência**: Algoritmo baseado em regras é explicável
2. **Controle**: Ajustes finos são mais fáceis
3. **Dados**: ML requer muitos dados de treino
4. **Performance**: Cálculos são rápidos e eficientes

### Vantagens da Abordagem Atual

✅ Resultados consistentes e previsíveis
✅ Fácil de debugar e ajustar
✅ Não requer dados de treino
✅ Performance excelente
✅ Extensível para adicionar mais fatores

### Quando usar ML?

🤖 Quando tiver muitos dados reais
🤖 Para padrões complexos não óbvios
🤖 Para aprendizado adaptativo
🤖 Para melhorar previsões ao longo do tempo

## 📚 Referências

- [UFC Stats](http://www.ufcstats.com/) - Dados reais para calibração
- [MMA Math](https://en.wikipedia.org/wiki/MMA_Math) - Conceitos de matchup
- [Elo Rating System](https://en.wikipedia.org/wiki/Elo_rating_system) - Sistema de rating
- [Monte Carlo Methods](https://en.wikipedia.org/wiki/Monte_Carlo_method) - Simulação estatística

---

**O algoritmo busca o equilíbrio entre realismo estatístico e aleatoriedade natural do MMA! 🥊**
