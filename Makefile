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
