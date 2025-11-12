# 🎯 Exemplos Práticos - FightBase API

## 🚀 Início Rápido - Primeiros Passos

### 1. 📝 Criar Conta

```bash
curl -X POST "http://localhost:8000/api/v1/customers" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "MMA Fan",
    "email": "fan@mma.com",
    "password": "senha123"
  }'
```

### 2. 🔐 Fazer Login

```bash
curl -X POST "http://localhost:8000/api/v1/auth/token" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "fan@mma.com",
    "password": "senha123"
  }'
```

**Resposta:**

```json
{
  "access_token": "YOUR_JWT_TOKEN_HERE",
  "token_type": "bearer"
}
```

**⚠️ Importante:** Salve o `access_token` para usar nos próximos requests!

## 🥋 Gerenciamento de Lutadores

### Criar Lutador - Jon Jones

```bash
curl -X POST "http://localhost:8000/api/v1/fighters" \
  -H "Authorization: Bearer <your_token_here>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Jon Jones",
    "nickname": "Bones",
    "organization": "UFC",
    "weight_class": "Peso-pesado",
    "fighting_style": "All-around",
    "striking": 92,
    "grappling": 95,
    "defense": 88,
    "stamina": 90,
    "speed": 85,
    "strategy": 98,
    "wins": 27,
    "losses": 1,
    "draws": 0,
    "ko_wins": 10,
    "submission_wins": 6,
    "age": 36,
    "height_cm": 193,
    "reach_cm": 215,
    "bio": "Ex-campeão dos meio-pesados, considerado um dos maiores de todos os tempos",
    "is_real": true
  }'
```

### Criar Lutador - Khabib Nurmagomedov

```bash
curl -X POST "http://localhost:8000/api/v1/fighters" \
  -H "Authorization: Bearer <your_token_here>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Khabib Nurmagomedov",
    "nickname": "The Eagle",
    "organization": "UFC",
    "weight_class": "Peso-leve",
    "fighting_style": "Grappler",
    "striking": 78,
    "grappling": 98,
    "defense": 92,
    "stamina": 95,
    "speed": 82,
    "strategy": 96,
    "wins": 29,
    "losses": 0,
    "draws": 0,
    "ko_wins": 8,
    "submission_wins": 11,
    "age": 35,
    "height_cm": 178,
    "reach_cm": 178,
    "bio": "Campeão invicto dos leves, domínio total no grappling",
    "is_real": true
  }'
```

### Criar Lutador Fictício

```bash
curl -X POST "http://localhost:8000/api/v1/fighters" \
  -H "Authorization: Bearer <your_token_here>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Bruce Wayne",
    "nickname": "The Dark Knight",
    "organization": "Custom",
    "weight_class": "Peso-médio",
    "fighting_style": "All-around",
    "striking": 95,
    "grappling": 90,
    "defense": 100,
    "stamina": 98,
    "speed": 97,
    "strategy": 100,
    "wins": 100,
    "losses": 0,
    "is_real": false,
    "bio": "O Cavaleiro das Trevas testando suas habilidades no octógono"
  }'
```

### Buscar Lutadores

#### Por Nome

```bash
curl "http://localhost:8000/api/v1/fighters?name=Jones"
```

#### Por Organização

```bash
curl "http://localhost:8000/api/v1/fighters?organization=UFC&limit=20"
```

#### Por Categoria de Peso

```bash
curl "http://localhost:8000/api/v1/fighters?weight_class=Peso-leve"
```

#### Lutadores Reais vs Fictícios

```bash
# Apenas reais
curl "http://localhost:8000/api/v1/fighters?is_real=true"

# Apenas fictícios
curl "http://localhost:8000/api/v1/fighters?is_real=false"
```

#### Rating Mínimo

```bash
curl "http://localhost:8000/api/v1/fighters?min_overall=90"
```

### Ver Meus Lutadores

```bash
curl "http://localhost:8000/api/v1/fighters/my/fighters" \
  -H "Authorization: Bearer <your_token_here>"
```

### Top Lutadores

#### Top 10 Geral

```bash
curl "http://localhost:8000/api/v1/fighters/rankings/top?limit=10"
```

#### Top 10 do UFC

```bash
curl "http://localhost:8000/api/v1/fighters/rankings/top?organization=UFC&limit=10"
```

#### Top 5 dos Peso-pesado

```bash
curl "http://localhost:8000/api/v1/fighters/rankings/top?weight_class=Peso-pesado&limit=5"
```

### Estatísticas Gerais

```bash
curl "http://localhost:8000/api/v1/fighters/statistics/overview"
```

**Resposta exemplo:**

```json
{
  "total_fighters": 50,
  "total_real": 40,
  "total_fictional": 10,
  "organizations": {
    "UFC": 30,
    "Bellator": 8,
    "ONE": 5,
    "Custom": 7
  },
  "weight_classes": {
    "Peso-pesado": 10,
    "Peso-médio": 15,
    "Peso-leve": 12,
    "Peso-pena": 8,
    "Peso-galo": 5
  },
  "avg_overall_rating": 85.4
}
```

## ⚔️ Simulação de Lutas

### Simular Luta Completa

```bash
curl -X POST "http://localhost:8000/api/v1/simulations" \
  -H "Authorization: Bearer <your_token_here>" \
  -H "Content-Type: application/json" \
  -d '{
    "fighter1_id": "uuid-do-jon-jones",
    "fighter2_id": "uuid-do-khabib",
    "rounds": 5,
    "notes": "Superfight - Meio-pesado vs Leve"
  }'
```

**Resposta exemplo:**

```json
{
  "id": "simulation-uuid",
  "fighter1_id": "jones-uuid",
  "fighter2_id": "khabib-uuid",
  "fighter1_name": "Jon Jones",
  "fighter2_name": "Khabib Nurmagomedov",
  "winner_id": "jones-uuid",
  "winner_name": "Jon Jones",
  "result_type": "Decision",
  "rounds": 5,
  "finish_round": null,
  "fighter1_probability": 62.5,
  "fighter2_probability": 37.5,
  "simulation_details": {
    "rounds": [
      {
        "round_number": 1,
        "fighter1_points": 85.4,
        "fighter2_points": 78.2,
        "dominant_fighter": "Jon Jones",
        "events": [
          "Jon Jones dominou o round",
          "Jon Jones acertou um golpe significativo"
        ]
      },
      {
        "round_number": 2,
        "fighter1_points": 82.1,
        "fighter2_points": 88.5,
        "dominant_fighter": "Khabib Nurmagomedov",
        "events": ["Khabib Nurmagomedov conseguiu um takedown"]
      }
      // ... mais rounds
    ],
    "total_points": {
      "fighter1": 425.8,
      "fighter2": 402.3
    }
  },
  "notes": "Superfight - Meio-pesado vs Leve",
  "created_at": "2025-11-10T12:30:00Z"
}
```

### Prever Resultado (Sem Simular)

```bash
curl "http://localhost:8000/api/v1/simulations/predict?fighter1_id=jones-uuid&fighter2_id=khabib-uuid"
```

**Resposta exemplo:**

```json
{
  "fighter1_id": "jones-uuid",
  "fighter2_id": "khabib-uuid",
  "fighter1_name": "Jon Jones",
  "fighter2_name": "Khabib Nurmagomedov",
  "fighter1_win_probability": 62.5,
  "fighter2_win_probability": 37.5,
  "draw_probability": 0.0,
  "ko_probability": 35.8,
  "submission_probability": 28.4,
  "decision_probability": 35.8,
  "striking_advantage": "Jon Jones",
  "grappling_advantage": "Khabib Nurmagomedov",
  "overall_advantage": "Jon Jones",
  "analysis": "Jon Jones é o claro favorito nesta luta. Jon Jones tem vantagem significativa no striking.",
  "key_factors": [
    "Cardio de Khabib Nurmagomedov pode ser decisivo",
    "QI de luta de Jon Jones pode fazer a diferença"
  ]
}
```

### Comparar Lutadores

```bash
curl "http://localhost:8000/api/v1/simulations/compare?fighter1_id=jones-uuid&fighter2_id=khabib-uuid"
```

**Resposta exemplo:**

```json
{
  "fighter1": {
    "id": "jones-uuid",
    "name": "Jon Jones",
    "record": "27-1-0"
  },
  "fighter2": {
    "id": "khabib-uuid",
    "name": "Khabib Nurmagomedov",
    "record": "29-0-0"
  },
  "comparisons": {
    "striking": {
      "fighter1": 92,
      "fighter2": 78,
      "advantage": "Jon Jones",
      "diff": 14
    },
    "grappling": {
      "fighter1": 95,
      "fighter2": 98,
      "advantage": "Khabib Nurmagomedov",
      "diff": 3
    },
    "defense": {
      "fighter1": 88,
      "fighter2": 92,
      "advantage": "Khabib Nurmagomedov",
      "diff": 4
    },
    "stamina": {
      "fighter1": 90,
      "fighter2": 95,
      "advantage": "Khabib Nurmagomedov",
      "diff": 5
    },
    "speed": {
      "fighter1": 85,
      "fighter2": 82,
      "advantage": "Jon Jones",
      "diff": 3
    },
    "strategy": {
      "fighter1": 98,
      "fighter2": 96,
      "advantage": "Jon Jones",
      "diff": 2
    },
    "overall": {
      "fighter1": 91.3,
      "fighter2": 90.2,
      "advantage": "Jon Jones",
      "diff": 1.1
    }
  }
}
```

### Ver Histórico de um Lutador

```bash
curl "http://localhost:8000/api/v1/simulations/history/jones-uuid?limit=20"
```

**Resposta exemplo:**

```json
{
  "fighter_id": "jones-uuid",
  "fighter_name": "Jon Jones",
  "statistics": {
    "total_fights": 15,
    "wins": 12,
    "losses": 3,
    "win_rate": 80.0,
    "ko_wins": 5,
    "submission_wins": 3,
    "decision_wins": 4
  },
  "recent_fights": [
    {
      "id": "sim-uuid-1",
      "fighter1_name": "Jon Jones",
      "fighter2_name": "Stipe Miocic",
      "winner_name": "Jon Jones",
      "result_type": "Submission",
      "rounds": 5,
      "finish_round": 3,
      "created_at": "2025-11-10T10:00:00Z"
    }
    // ... mais lutas
  ],
  "pagination": {
    "limit": 20,
    "offset": 0,
    "total": 15
  }
}
```

### Ver Confrontos Diretos

```bash
curl "http://localhost:8000/api/v1/simulations/matchup?fighter1_id=jones-uuid&fighter2_id=cormier-uuid"
```

### Ver Simulações Recentes

```bash
curl "http://localhost:8000/api/v1/simulations/recent?limit=50"
```

## 🎯 Cenários de Uso Completos

### Cenário 1: "E se Anderson Silva lutasse com Jon Jones?"

```bash
# 1. Criar Anderson Silva
curl -X POST "http://localhost:8000/api/v1/fighters" \
  -H "Authorization: Bearer <your_token_here>" \
  -d '{
    "name": "Anderson Silva",
    "organization": "UFC",
    "weight_class": "Peso-médio",
    "fighting_style": "Striker",
    "striking": 98,
    "grappling": 85,
    "defense": 82,
    "stamina": 88,
    "speed": 92,
    "strategy": 95,
    "wins": 34,
    "losses": 11,
    "is_real": true
  }'

# 2. Comparar
curl "http://localhost:8000/api/v1/simulations/compare?fighter1_id=silva-uuid&fighter2_id=jones-uuid"

# 3. Ver previsão
curl "http://localhost:8000/api/v1/simulations/predict?fighter1_id=silva-uuid&fighter2_id=jones-uuid"

# 4. Simular luta de 5 rounds
curl -X POST "http://localhost:8000/api/v1/simulations" \
  -H "Authorization: Bearer <your_token_here>" \
  -d '{
    "fighter1_id": "silva-uuid",
    "fighter2_id": "jones-uuid",
    "rounds": 5,
    "notes": "Anderson Silva no auge vs Jon Jones"
  }'
```

### Cenário 2: Criar Ranking do UFC Peso-médio

```bash
# 1. Criar vários lutadores peso-médio
# ... (criar Israel Adesanya, Robert Whittaker, etc)

# 2. Ver top 10
curl "http://localhost:8000/api/v1/fighters/rankings/top?organization=UFC&weight_class=Peso-médio&limit=10"

# 3. Simular campeonato (semifinais + final)
# Semifinal 1
curl -X POST "http://localhost:8000/api/v1/simulations" ...

# Semifinal 2
curl -X POST "http://localhost:8000/api/v1/simulations" ...

# Final
curl -X POST "http://localhost:8000/api/v1/simulations" ...
```

### Cenário 3: Testar seu Lutador Personalizado

```bash
# 1. Criar lutador fictício
curl -X POST "http://localhost:8000/api/v1/fighters" \
  -H "Authorization: Bearer <your_token_here>" \
  -d '{
    "name": "Seu Nome",
    "organization": "Custom",
    "weight_class": "Peso-médio",
    "fighting_style": "All-around",
    "striking": 95,
    "grappling": 95,
    "defense": 90,
    "stamina": 95,
    "speed": 90,
    "strategy": 95,
    "is_real": false
  }'

# 2. Testar contra os melhores
curl "http://localhost:8000/api/v1/fighters/rankings/top?weight_class=Peso-médio&limit=5"

# 3. Simular contra cada um
curl -X POST "http://localhost:8000/api/v1/simulations" ...
```

## 🔍 Dicas e Truques

### 1. Balance de Atributos

Para criar lutadores balanceados:

- **Striker**: Striking 90+, Speed 85+, Defense 80+
- **Grappler**: Grappling 90+, Stamina 85+, Strategy 85+
- **All-around**: Todos os atributos entre 80-95

### 2. Overall Rating

O overall é calculado automaticamente:

```
Overall = (striking + grappling + defense + stamina + speed + strategy) / 6
```

### 3. Probabilidades

- Diferença de 5-10 pontos: Luta equilibrada (~55-45%)
- Diferença de 10-20 pontos: Favorito claro (~65-35%)
- Diferença de 20+ pontos: Dominação (~75-25%)

### 4. Tipos de Resultado

- **KO**: Mais provável quando striker vs grappler
- **Submission**: Mais provável quando grappler domina
- **Decision**: Mais provável em lutas equilibradas

## 🐛 Troubleshooting

### Erro: "Fighter not found"

```bash
# Verifique se o UUID está correto
curl "http://localhost:8000/api/v1/fighters/UUID_AQUI"
```

### Erro: "Unauthorized"

```bash
# Verifique se o token está válido
# Faça login novamente se necessário
```

### Erro: "Fighter with name already exists"

```bash
# Use outro nome ou adicione apelido diferenciador
```

## 📊 Monitorando Resultados

### Ver todas as suas simulações

```bash
curl "http://localhost:8000/api/v1/simulations/recent?limit=100" \
  -H "Authorization: Bearer <your_token_here>"
```

### Estatísticas de um lutador

```bash
curl "http://localhost:8000/api/v1/simulations/history/fighter-uuid"
```

---

**Divirta-se criando e simulando lutas! 🥊**
