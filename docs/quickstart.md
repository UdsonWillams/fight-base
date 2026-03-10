# 🥊 FightBase - Quick Start Guide

## ⚡ Início Rápido

### 1. Configure o Ambiente

```bash
cp .env.example .env
# Edite o .env com suas credenciais se necessário

python -m venv .venv
.venv\Scripts\activate       # Windows
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 2. Suba os Serviços (Banco + Cache)

```bash
docker compose up database redis -d
```

> O banco de dados sobe na porta `5432` e o Redis na `6379`.

### 3. Suba a API

```bash
uvicorn app.main:app --reload --host=localhost --port=8080
```

> As migrations são aplicadas automaticamente no startup.
> API disponível em: http://localhost:8080
> Swagger em: http://localhost:8080/docs

---

## 📦 Populando o Banco com Dados Reais (UFC Stats)

### Passo 1 — Scrape dos dados

Execute o script de scraping para baixar todos os dados do UFC:

```bash
python scripts/scrape_dataset.py
```

> Isso pode levar **30-60 minutos** (são ~750 eventos e ~8000 lutas).
> Os arquivos serão salvos em: `datasets/fighter_details.csv`, `datasets/fight_details.csv`, `datasets/event_details.csv` e `datasets/UFC.csv`.

### Passo 2 — Importação para o banco

Com a API e o banco rodando, execute:

```bash
# No Linux/Mac:
bash scripts/run_import.sh

# No Windows (Git Bash / WSL):
bash scripts/run_import.sh

# Ou diretamente via Python:
python scripts/import_ufc_dataset.py
```

> O `run_import.sh` valida os CSVs, aplica as migrations e importa os dados.

---

## 🐛 Problemas Comuns

### `Connection Refused` no startup da API

```bash
# Verifique se os containers estão de pé
docker compose ps

# Se não estiverem, reinicie limpando os volumes corrompidos
docker compose down -v
docker compose up database redis -d
```

### `No such revision` no Alembic

Significa que o banco tem um histórico de migração antigo e corrompido. Solução:

```bash
docker compose down -v   # limpa os volumes do banco
docker compose up database redis -d
```

### API subindo mas Swagger em branco

Garanta que a porta 8080 não está sendo usada por outro processo e use o endereço correto:
- ✅ `http://localhost:8080/docs`
- ❌ `http://localhost:8000`

---

## 📊 Endpoints Principais

| Método | Endpoint                        | Descrição         |
| ------ | ------------------------------- | ----------------- |
| GET    | `/api/v1/fighters`              | Lista lutadores   |
| POST   | `/api/v1/fighters`              | Cria lutador      |
| GET    | `/api/v1/fighters/rankings/top` | Top ranqueados    |
| POST   | `/api/v1/simulations`           | Simula luta       |
| GET    | `/api/v1/simulations/predict`   | Prevê resultado   |
| GET    | `/api/v1/simulations/compare`   | Compara lutadores |


## ⚡ Início Rápido (5 minutos)

### 1. Clone e Configure

```bash
cd /home/udson-rego/Documentos/estudos/fight-base/fight-base
cp .env.example .env
```

### 2. Inicie com Docker

```bash
docker-compose up --build
```

### 3. Execute Migrations

```bash
# Em outro terminal
docker-compose exec app alembic upgrade head
```

### 4. Crie Admin

```bash
docker-compose exec app python scripts/create_admin.py
```

### 5. Acesse!

- 🌐 API: http://localhost:8000
- 📚 Swagger: http://localhost:8000/swagger
- 📖 Docs: http://localhost:8000/docs

## 🎯 Teste Rápido no Swagger

### Passo 1: Fazer Login

1. Vá para `/api/v1/auth/token` no Swagger
2. Clique em "Try it out"
3. Use: `admin@mail.com` / `pass@word`
4. Execute e copie o `access_token`

### Passo 2: Autorizar

1. Clique no botão "Authorize" (cadeado no topo)
2. Cole o token
3. Clique em "Authorize"

### Passo 3: Criar Lutador

1. Vá para `POST /api/v1/fighters`
2. Clique em "Try it out"
3. Use este exemplo:

```json
{
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
  "is_real": true
}
```

4. Execute e salve o `id` retornado

### Passo 4: Criar Outro Lutador

Repita o passo 3 com:

```json
{
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
  "is_real": true
}
```

### Passo 5: Simular Luta! 🎮

1. Vá para `POST /api/v1/simulations`
2. Use os IDs dos lutadores criados:

```json
{
  "fighter1_id": "uuid-do-jon-jones",
  "fighter2_id": "uuid-do-khabib",
  "rounds": 5,
  "notes": "Superfight imaginária!"
}
```

3. Execute e veja o resultado! 🥊

## 📊 Endpoints Principais

| Método | Endpoint                        | Descrição         |
| ------ | ------------------------------- | ----------------- |
| GET    | `/api/v1/fighters`              | Lista lutadores   |
| POST   | `/api/v1/fighters`              | Cria lutador      |
| GET    | `/api/v1/fighters/rankings/top` | Top ranqueados    |
| POST   | `/api/v1/simulations`           | Simula luta       |
| GET    | `/api/v1/simulations/predict`   | Prevê resultado   |
| GET    | `/api/v1/simulations/compare`   | Compara lutadores |

## 🎓 Próximos Passos

1. ✅ Leia o [README.md](README.md) completo
2. 📚 Veja [EXEMPLOS_PRATICOS.md](docs/EXEMPLOS_PRATICOS.md)
3. 🧠 Entenda o [ALGORITMO_TECNICO.md](docs/ALGORITMO_TECNICO.md)
4. 💡 Explore [CASOS_DE_USO.md](docs/CASOS_DE_USO.md)
5. 🚀 Siga [PROXIMOS_PASSOS.md](PROXIMOS_PASSOS.md)

## 🐛 Problemas Comuns

### Erro: "Port 8000 already in use"

```bash
# Mate o processo usando a porta
sudo lsof -ti:8000 | xargs kill -9
```

### Erro: "Database connection failed"

```bash
# Verifique se o PostgreSQL está rodando
docker-compose ps
# Reinicie os containers
docker-compose down && docker-compose up
```

### Erro: "Unauthorized"

```bash
# Faça login novamente e use o token correto
# Token expira em 30 minutos (padrão)
```

## 💬 Suporte

- 📧 Issues: [GitHub Issues](https://github.com/UdsonWillams/fight-base/issues)
- 📖 Docs: Leia os arquivos na pasta `/docs`
- 💡 Ideias: Abra uma Issue com label "enhancement"

## 🎉 Pronto!

Agora você tem um sistema completo de simulação de lutas MMA rodando!

**Divirta-se criando lutadores e simulando lutas épicas! 🥊**
