# 🥊 Guia Rápido - Importação Dataset UFC

## 📋 Checklist Pré-Importação

- [ ] Arquivos CSV na raiz do projeto:
  - `fighter_details.csv`
  - `event_details.csv`
  - `fight_details.csv`
- [ ] Banco de dados configurado (PostgreSQL)
- [ ] Ambiente conda ativado: `conda activate fight-base`

## 🚀 Importação Rápida

### Opção 1: Script Automático (Recomendado)

```bash
./scripts/run_import.sh
```

### Opção 2: Manual

```bash
# 1. Aplicar migrations
alembic upgrade head

# 2. Executar importação
python scripts/import_ufc_dataset.py

# 3. Validar dados
python scripts/validate_import.py

# 4. Ver exemplos
python scripts/example_ufc_queries.py
```

## 📊 O Que Será Importado

| Entidade   | Quantidade Estimada | Descrição                          |
|------------|--------------------:|-------------------------------------|
| Lutadores  | ~2.600             | Dados biográficos e estatísticas    |
| Eventos    | ~750               | Cards UFC de 1994 a 2025            |
| Lutas      | ~8.300             | Estatísticas detalhadas de combates |

## ✅ Validação

Após importação, o script mostra:

```
============================================================
📊 ESTATÍSTICAS DA IMPORTAÇÃO
============================================================
✓ Lutadores criados:     2611
✓ Lutadores atualizados: 0
✓ Eventos criados:       752
✓ Lutas criadas:         8337
============================================================
```

Execute a validação:
```bash
python scripts/validate_import.py
```

## 🔍 Consultas Úteis

### Via Python

```python
from app.database.models.base import Fighter, Event, Fight
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Buscar lutador por nome
fighter = session.query(Fighter).filter(
    Fighter.name.ilike('%conor%mcgregor%')
).first()

print(f"Record: {fighter.wins}-{fighter.losses}-{fighter.draws}")
print(f"Cartel: {len(fighter.cartel)} lutas")
```

### Scripts Prontos

```bash
# Exemplos de queries
python scripts/example_ufc_queries.py
```

## 🎯 Novos Campos Disponíveis

### Fighters
- **Biográficos**: `date_of_birth`, `stance`, `height_cm`, `reach_cm`, `weight_lbs`
- **Stats UFC**: `slpm`, `str_acc`, `sapm`, `str_def`, `td_avg`, `td_acc`, `td_def`, `sub_avg`
- **Cartel**: Lista de lutas em `cartel` field (JSONB)

### Events
- **ID UFC Stats**: `ufcstats_id` para validação

### Fights
- **Detalhes**: `referee`, `match_time_seconds`
- **Red Corner**: `r_kd`, `r_sig_str_landed`, `r_td_landed`, etc
- **Blue Corner**: `b_kd`, `b_sig_str_landed`, `b_td_landed`, etc

## 🔗 Verificação de Dados

Todos os registros podem ser verificados no site oficial:

- **Fighter**: `http://ufcstats.com/fighter-details/{ufcstats_id}`
- **Event**: `http://ufcstats.com/event-details/{ufcstats_id}`
- **Fight**: `http://ufcstats.com/fight-details/{ufcstats_id}`

## ⚡ Tempo de Importação

- **Lutadores**: ~30-60 segundos
- **Eventos**: ~10-20 segundos
- **Lutas**: ~1-3 minutos
- **Cartéis**: ~30-60 segundos
- **Total**: ~2-5 minutos

## 🛠️ Troubleshooting

### Erro: "CSV não encontrado"
```bash
# Verifique se está na raiz do projeto
ls -la *.csv

# Se não, mova os arquivos
mv ~/Downloads/*.csv .
```

### Erro: "Database connection"
```bash
# Verifique .env
cat .env | grep DATABASE

# Teste conexão
python -c "from app.core.settings import Settings; print(Settings().SQLALCHEMY_DATABASE_URI)"
```

### Erro: "Migration failed"
```bash
# Limpar e refazer migrations
alembic downgrade base
alembic upgrade head
```

### Re-importar dados
```bash
# Deletar dados UFC existentes e reimportar
python -c "
from app.database.models.base import Fighter, Event, Fight
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.settings import Settings

engine = create_engine(Settings().SQLALCHEMY_DATABASE_URI)
Session = sessionmaker(bind=engine)
session = Session()

session.query(Fight).filter(Fight.ufcstats_id.isnot(None)).delete()
session.query(Event).filter(Event.ufcstats_id.isnot(None)).delete()
session.query(Fighter).filter(Fighter.ufcstats_id.isnot(None)).delete()
session.commit()
print('✓ Dados UFC removidos')
"

# Agora reimporte
python scripts/import_ufc_dataset.py
```

## 📖 Documentação Completa

Para mais detalhes, consulte:
- `docs/importacao-ufc-dataset.md` - Guia completo
- `DATASET_INTEGRATION_SUMMARY.md` - Resumo técnico

---

**Dúvidas?** Consulte a documentação ou execute os exemplos em `scripts/example_ufc_queries.py`
