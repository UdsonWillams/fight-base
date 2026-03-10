# FightBase Makefile - Comando de Gestão Local

.PHONY: setup up down restart db server migrate logs test clean status

# 🛠️ Setup inicial: Instala dependências e gera .env
setup:
	@echo "🔧 Iniciando setup local..."
	@if [ ! -f .env ]; then cp .env.example .env && echo "✅ Arquivo .env criado a partir do template."; else echo "⚠️  Arquivo .env já existe, pulando cópia."; fi
	pip install -r requirements.txt
	@echo "✅ Dependências instaladas com sucesso!"

# 🚀 Sobe todo o ecossistema (Banco + Backend com hot-reload)
up:
	@echo "⬆️  Subindo containers..."
	docker compose up -d database
	@echo "⏳ Aguardando banco de dados iniciar..."
	@sleep 5
	@echo "🥊 Iniciando backend..."
	uvicorn app.main:app --reload --host=0.0.0.0 --port=8080

# ⏹️ Para todos os containers
down:
	@echo "⬇️  Parando containers..."
	docker compose down

# 🔄 Reinicia o sistema
restart: down up

# 🗄️ Sobe apenas o banco de dados
db:
	@echo "🗄️ Iniciando banco de dados..."
	docker compose up -d database

# ⚡ Sobe apenas o servidor backend (útil se o banco já estiver rodando)
server:
	@echo "⚡ Iniciando servidor backend..."
	uvicorn app.main:app --reload --host=0.0.0.0 --port=8080

# 🛣️ Gera uma nova migration do Alembic
# Uso: make migrate message="descricao da mudança"
migrate:
	@if [ -z "$(message)" ]; then echo "❌ Erro: Use make migrate message='minha descricao'"; exit 1; fi
	alembic revision --autogenerate -m "$(message)"
	@echo "✅ Migration criada com sucesso!"

# 📜 Mostra logs do banco de dados
logs:
	docker compose logs -f database

# 🧪 Roda os testes unitários com cobertura
test:
	@echo "🧪 Executando testes..."
	PYTHONPATH=. pytest --cov=app --cov-report=term-missing --disable-warnings

# 🧹 Limpeza total: Para containers e remove VOLUMES (reseta o banco)
clean:
	@echo "🧹 Limpando ambiente..."
	docker compose down -v
	@echo "✅ Ambiente limpo e volumes removidos!"

# 📊 Status dos containers
status:
	docker compose ps
.PHONY: runserver runfrontend coverage migrations scrape import

runserver:
	docker compose up database redis -d
	uvicorn app.main:app --reload --host=localhost --port=8080

runfrontend:
	cd frontend; python -m http.server 3000

coverage:
	python -m pytest --cov=app --cov-report=xml --cov-fail-under=55 --disable-warnings

migrations:
	alembic revision --autogenerate -m $(message)
	@echo "Migrations created successfully"
	@echo "Don't forget to edit the new migration file if necessary"

scrape:
	python scripts/scrape_dataset.py

import:
	python scripts/import_ufc_dataset.py
