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
```python
- ufcstats_id: ID único do ufcstats.com
- name, nickname
- date_of_birth, stance
- height_cm/inches, reach_cm/inches, weight_lbs
- wins, losses, draws
- slpm, str_acc, sapm, str_def
- td_avg, td_acc, td_def, sub_avg
- striking, grappling, defense, stamina, speed, strategy (calculados)
```

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

### 4. **Atualiza Cartéis**
- Constrói o histórico de lutas (cartel) de cada lutador
- Formato: Lista de dicionários com opponent, result, method, round, org

### 5. **Atualiza Nomes dos Eventos**
- Extrai nomes reais dos eventos do fight_details.csv
- Ex: "UFC Fight Night: Imavov vs. Borralho"

## 🚀 Como Usar

### Pré-requisitos
1. Ter os arquivos CSV na raiz do projeto:
   ```
   fighter_details.csv
   event_details.csv
   fight_details.csv
   ```

2. Banco de dados configurado e migrations aplicadas:
   ```bash
   make migrate
   ```

### Executar Importação

```bash
# Ativar ambiente
conda activate fight-base

# Executar script
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
3. ✅ Criar endpoints para estatísticas históricas
4. ✅ Implementar análise de matchups baseada em dados reais
