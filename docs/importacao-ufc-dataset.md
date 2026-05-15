# Importação do Dataset UFC

Script para importar dados históricos do UFC (1994-2025) no banco de dados do FightBase.

## 📦 Dataset Fonte

O dataset contém informações de **ufcstats.com**:

- **fighter_details.csv**: Dados biográficos e estatísticas dos lutadores
- **event_details.csv**: Informações sobre eventos UFC
- **fight_details.csv**: Detalhes completos de cada luta

## 🎯 O que o Script Faz

### 1. **Importa Lutadores** (`fighter_details.csv`)

- Cria/atualiza lutadores reais do UFC
- Mapeia estatísticas avançadas (SLPM, Str Acc, TD Avg, etc)
- Calcula atributos do sistema (0-100) baseados nas stats
- Armazena dados biográficos (data de nascimento, stance, altura, alcance)

**Campos importados:**
<div style="font-family: monospace;">

```
- ufcstats_id: ID único do ufcstats.com
- name, nickname
- date_of_birth, stance
- height_cm/inches, reach_cm/inches, weight_lbs
- wins, losses, draws
- slpm, str_acc, sapm, str_def
- td_avg, td_acc, td_def, sub_avg
- kd_avg
- ko_wins, submission_wins
- fighting_style
- striking, grappling, defense, stamina, speed, strategy (calculados)
```
</div>

### 2. **Importa Eventos** (`event_details.csv`)

- Cria eventos UFC com data e localização
- Mapeia IDs para relacionamentos

**Campos importados:**

```python
- ufcstats_id: ID único do evento
- name: Nome do evento (atualizado depois via fight_details)
- date, location
- organization: 'UFC'
- status: 'completed'
```

### 3. **Importa Lutas** (`fight_details.csv`)

- Cria lutas vinculando fighters e events pelos IDs
- Importa estatísticas completas round-a-round
- Preserva red/blue corner

**Campos importados:**

```python
- ufcstats_id: ID único da luta
- event_id, fighter1_id (red), fighter2_id (blue)
- weight_class, rounds, is_title_fight
- result_type, finish_round, method_details
- match_time_seconds, referee
- r_* : Estatísticas Red Corner (fighter1)
- b_* : Estatísticas Blue Corner (fighter2)
  - kd, sig_str_landed/attempted
  - total_str_landed/attempted
  - td_landed/attempted
  - sub_att, ctrl_seconds
```

### 4. **Agrega ML Stats dos Lutadores**
- Agrega estatísticas por luta da tabela `Fight` para cada lutador
- Calcula SLPM, Str Acc, SAPM, Str Def, TD Avg, TD Acc, TD Def, Sub Avg
- Calcula KD Avg (knockdowns por luta)
- Conta KO Wins e Submission Wins a partir dos métodos de vitória
- Infere `fighting_style` (Striker / Grappler / MMA)

**Campos populados:**

```python
- slpm: Σ sig_str_landed / Σ (match_time / 60)
- str_acc: Σ sig_str_landed / Σ sig_str_attempted * 100
- sapm: Σ opponent_sig_str_landed / Σ (match_time / 60)
- str_def: 100 - (Σ opp_sig_str_landed / Σ opp_sig_str_attempted * 100)
- td_avg: Σ td_landed / Σ (match_time / 900)   # por 15 min
- td_acc: Σ td_landed / Σ td_attempted * 100
- td_def: 100 - (Σ opp_td_landed / Σ opp_td_attempted * 100)
- sub_avg: Σ sub_att / Σ (match_time / 900)     # por 15 min
- kd_avg: Σ kd_landed / total_fights
- ko_wins: contagem de vitórias por KO/TKO
- submission_wins: contagem de vitórias por Submission
- fighting_style: Striker | Grappler | MMA
```

### 5. **Atualiza Cartéis**

- Constrói o histórico de lutas (cartel) de cada lutador
- Formato: Lista de dicionários com opponent, result, method, round, org
- Popula `last_fight_date` com a data da luta mais recente

### 6. **Atualiza Nomes dos Eventos**

- Extrai nomes reais dos eventos do fight_details.csv
- Ex: "UFC Fight Night: Imavov vs. Borralho"

## 🚀 Como Usar

### Pré-requisitos

1. Banco de dados configurado e migrations aplicadas:
   ```bash
   make migrations
   ```

### 1. Extrair os Dados Mais Recentes (Opcional)

Caso queira atualizar os arquivos locais com os resultados mais recentes desde a última execução, execute o scraper assíncrono:

```bash
make scrape
```
*(Isso irá capturar todos os dados do portal ufcstats.com e atualizar a pasta `datasets/` com os arquivos `fighter_details.csv`, `event_details.csv`, `fight_details.csv` e o consolidado `UFC.csv`)*

### 2. Executar Importação para o DB

Após extrair os dados (ou caso já possua os arquivos do dataset na pasta /datasets), utilize o script de importação:

```bash
python scripts/import_ufc_dataset.py
```

## 📊 Saída Esperada

```
🥊 IMPORTADOR DE DATASET UFC
============================================================
✓ Usuário do sistema criado

📥 Importando lutadores de fighter_details.csv...
  ⏳ Processados 100 lutadores...
  ⏳ Processados 200 lutadores...
  ...
✓ Lutadores importados: 4523 criados, 0 atualizados

📥 Importando eventos de event_details.csv...
✓ Eventos importados: 752

📥 Importando lutas de fight_details.csv...
  ⏳ Processadas 100 lutas...
  ⏳ Processadas 200 lutas...
  ...
✓ Lutas importadas: 8234

📊 Agregando ML stats para 4523 lutadores...
  ⏳ ML Stats: 200/4523 (4.4%) — ...
  ...
✓ ML stats atualizados para 4523 lutadores em XmXXs

📝 Atualizando nomes dos eventos...
✓ Nomes atualizados para 752 eventos

📊 Atualizando cartel dos lutadores...
✓ Cartéis atualizados para 4523 lutadores

============================================================
📊 ESTATÍSTICAS DA IMPORTAÇÃO
============================================================
✓ Lutadores criados:     4523
✓ Lutadores atualizados: 0
✓ Eventos criados:       752
✓ Lutas criadas:         8234
============================================================

✅ Importação concluída com sucesso!
```

## 🔄 Mapeamento de IDs

O script mantém três dicionários de mapeamento:

```python
self.fighter_id_map: Dict[str, UUID]  # ufcstats_id -> UUID
self.event_id_map: Dict[str, UUID]    # ufcstats_id -> UUID
self.fight_id_map: Dict[str, UUID]    # ufcstats_id -> UUID
```

Isso permite:

- ✅ Relacionar lutas com lutadores e eventos corretos
- ✅ Construir cartéis precisos
- ✅ Verificar dados no ufcstats.com: `http://ufcstats.com/fighter-details/{ufcstats_id}`

## 🎨 Cálculo de Atributos

Os atributos do sistema (0-100) são calculados baseados nas estatísticas reais:

```python
striking = min(100, int((slpm or 0) * 10 + (str_acc or 50)))
grappling = min(100, int((td_avg or 0) * 20 + (sub_avg or 0) * 30 + 30))
defense = min(100, int((str_def or 50) + (td_def or 50)) // 2)
stamina = min(100, 50 + total_fights)
speed = min(100, int((slpm or 3) * 15))
strategy = min(100, 50 + total_fights // 2)
```

## ⚠️ Observações

1. **Usuário System**: Cria automaticamente `system@fightbase.com` como criador dos lutadores reais
2. **Idempotência**: Script detecta registros existentes via `ufcstats_id`
3. **Erros**: Registra erros sem interromper importação; mostra resumo no final
4. **Performance**: Commit a cada 100 registros para otimizar

## 🔧 Troubleshooting

### Erro: "Arquivo não encontrado"

- Verifique se os CSVs estão na raiz do projeto

### Erro: "Foreign key constraint"

- Execute as migrations primeiro: `make migrate`

### Importação incompleta

- Verifique erros no final da execução
- Script continua mesmo com erros individuais

## 📈 Próximos Passos

Após importação bem-sucedida:

1. ✅ Validar dados importados via API
2. ✅ Usar estatísticas reais no algoritmo de simulação
3. ✅ Retreinar modelo ML com 18 features: `python scripts/train_model_local.py`
4. ✅ Criar endpoints para estatísticas históricas
5. ✅ Implementar análise de matchups baseada em dados reais
