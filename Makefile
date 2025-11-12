.PHONY: runserver runfrontend coverage migrations

runserver:
	docker compose up database -d
	uvicorn app.main:app --reload --host=localhost --port=8080

runfrontend:
	cd frontend && python3 -m http.server 3000

coverage:
	PYTHONPATH=. pytest --cov=app --cov-report=xml --cov-fail-under=55 --disable-warnings

migrations:
	alembic revision --autogenerate -m $(message)
	@echo "Migrations created successfully"
	@echo "Don't forget to edit the new migration file if necessary"
