# Sistema de Cartel de Lutadores

## 📋 Conceito

O sistema separa **cartel real** (vida real) de **estatísticas de simulações**.

### ✅ Cartel Real (`real_record`)

- Registra o histórico **REAL** do lutador (ex: UFC, Bellator)
- **NÃO é afetado** pelas simulações do sistema
- Campo opcional (pode ser `null` para lutadores fictícios)
- Formato:

```json
{
  "wins": 15,
  "losses": 3,
  "draws": 0,
  "ko_wins": 8,
  "submission_wins": 4
}
```

### 📊 Estatísticas de Simulações

- Calculadas dinamicamente a partir das simulações salvas
- **Separadas** do cartel real
- Usadas apenas para análise e diversão
- Acessadas via endpoint `/simulations/stats/{fighter_id}`

---

## 🎯 Exemplos de Uso

### 1. Criar Lutador Real (com cartel)

```json
POST /fighters
{
  "name": "Connor McGregor",
  "organization": "UFC",
  "weight_class": "Lightweight",
  "fighting_style": "Striker",
  "gender": "male",
  "striking": 95,
  "grappling": 75,
  "defense": 70,
  "stamina": 80,
  "speed": 90,
  "strategy": 85,
  "real_record": {
    "wins": 22,
    "losses": 6,
    "draws": 0,
    "ko_wins": 19,
    "submission_wins": 1
  },
  "is_real": true
}
```

**Resposta:**

```json
{
  "id": "abc-123",
  "name": "Connor McGregor",
  "real_record": {
    "wins": 22,
    "losses": 6,
    "draws": 0,
    "ko_wins": 19,
    "submission_wins": 1
  },
  "record": "22-6-0", // Computed field
  "overall_rating": 82.5
}
```

### 2. Criar Lutador Fictício (sem cartel)

```json
POST /fighters
{
  "name": "Shadow Fighter",
  "organization": "Custom",
  "weight_class": "Middleweight",
  "fighting_style": "Mixed",
  "gender": "male",
  "striking": 88,
  "grappling": 92,
  "defense": 85,
  "stamina": 90,
  "speed": 87,
  "strategy": 91,
  "real_record": null,  // Sem cartel real
  "is_real": false
}
```

**Resposta:**

```json
{
  "id": "xyz-789",
  "name": "Shadow Fighter",
  "real_record": null,
  "record": null, // Computed field retorna null
  "overall_rating": 88.8
}
```

### 3. Simular Luta (NÃO afeta cartel real)

```json
POST /simulations
{
  "fighter1_id": "abc-123",  // Connor (22-6)
  "fighter2_id": "xyz-789",  // Shadow
  "rounds": 5
}
```

**Resultado:**

- ✅ Simulação é salva
- ✅ Estatística de simulação é atualizada
- ❌ **Cartel real NÃO muda** (Connor continua 22-6)

### 4. Ver Cartel Real

```json
GET /fighters/abc-123

Response:
{
  "name": "Connor McGregor",
  "real_record": {
    "wins": 22,        // ← NUNCA MUDA por simulações
    "losses": 6,
    "ko_wins": 19
  },
  "record": "22-6-0"
}
```

### 5. Ver Estatísticas de Simulações

```json
GET /simulations/stats/abc-123

Response:
{
  "total_simulations": 45,
  "wins": 30,
  "losses": 15,
  "win_rate": 66.7,
  "ko_wins": 18,
  "submission_wins": 5,
  "decision_wins": 7,
  "finish_rate": 76.7,
  "avg_rounds": 3.2
}
```

**Importante:** Estes 30 wins são de **SIMULAÇÕES**, não do cartel real!

---

## 🔄 Fluxo Completo

```
1. Criar Lutador Real
   ├─ real_record = {wins: 22, losses: 6}  ✅ Manual
   └─ Salvo no Firestore

2. Simular Lutas
   ├─ Simula Connor vs Shadow → Connor vence
   ├─ Simula Connor vs Shadow → Shadow vence
   └─ Simulações salvas na collection "simulations"

3. Consultar Dados
   ├─ GET /fighters/abc-123
   │  └─ real_record: {wins: 22, losses: 6}  ← Não mudou!
   │
   └─ GET /simulations/stats/abc-123
      └─ wins: 1, losses: 1  ← Estatísticas de simulação
```

---

## 📊 Endpoints

| Endpoint                        | Descrição                          | Afeta Cartel Real? |
| ------------------------------- | ---------------------------------- | ------------------ |
| `POST /fighters`                | Cria lutador com `real_record`     | -                  |
| `PUT /fighters/{id}`            | Atualiza `real_record` manualmente | ✅ Sim (manual)    |
| `POST /simulations`             | Simula luta                        | ❌ Não             |
| `GET /fighters/{id}`            | Retorna lutador + `real_record`    | -                  |
| `GET /simulations/stats/{id}`   | Estatísticas de simulações         | -                  |
| `GET /simulations/history/{id}` | Histórico de simulações            | -                  |

---

## ⚠️ Regras de Negócio

1. **Simulações são SEPARADAS do cartel real**

   - Usado apenas para "what-if" scenarios
   - Não afeta o histórico oficial do lutador

2. **Cartel real é MANUAL**

   - Administrador atualiza quando lutador luta na vida real
   - Não há automação (é intencional)

3. **Lutadores fictícios NÃO têm cartel real**

   - `real_record = null`
   - Apenas estatísticas de simulações

4. **Probabilidades usam cartel real (se existir)**
   - Lutadores com bom cartel real ganham pequeno bônus (+3%)
   - Se `real_record = null`, usa apenas atributos

---

## 🎮 Caso de Uso: Usuário

**Cenário:** Usuário quer simular Connor vs Khabib

1. **Vê os lutadores:**

   - Connor: 22-6 (real_record)
   - Khabib: 29-0 (real_record)

2. **Simula 10 vezes:**

   - Khabib vence 7x
   - Connor vence 3x

3. **Consulta estatísticas de simulação:**

   - Connor: 3 wins, 7 losses (em simulações)
   - Khabib: 7 wins, 3 losses (em simulações)

4. **Verifica cartel real:**
   - Connor: **AINDA 22-6** ✅
   - Khabib: **AINDA 29-0** ✅

**Conclusão:** Simulações não afetam a história real dos lutadores!

---

## 🚀 Migração de Dados Existentes

Se você tem lutadores com `wins`/`losses` separados:

```python
# Script de migração
for fighter in fighters:
    if fighter.get("wins") is not None:
        fighter["real_record"] = {
            "wins": fighter.pop("wins"),
            "losses": fighter.pop("losses"),
            "draws": fighter.pop("draws", 0),
            "ko_wins": fighter.pop("ko_wins", 0),
            "submission_wins": fighter.pop("submission_wins", 0)
        }
    else:
        fighter["real_record"] = None
```

---

## 📝 Resumo

- ✅ `real_record` = Cartel REAL (vida real)
- ✅ `/simulations/stats` = Estatísticas de SIMULAÇÕES
- ✅ Simulações NÃO afetam cartel real
- ✅ Cartel real é atualizado MANUALMENTE
- ✅ Lutadores fictícios podem ter `real_record = null`
