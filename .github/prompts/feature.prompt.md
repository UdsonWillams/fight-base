---
description: "Implement a new feature following strict TDD workflow"
argument-hint: "[describe the feature you want to implement]"
---

You are implementing a feature with TDD. Follow these rules strictly.

## Architecture Rules
1. **View > Service > Repository** — mandatory. Views never call repositories directly.
2. **Views simple** — parameter declaration + service call + return. No business logic.
3. **Services by domain** — `app/services/<domain>/`.
4. **API versioned** — `app/api/v1/` with `__init__.py` aggregating routers.
5. **Subdomains** — nested routes get subdirectories.
6. **Schemas by domain** — `app/schemas/<domain>/requests.py` + `responses.py`.
7. **Core is shared** — `app/core/`: config, logger, exceptions, security.
8. **Exceptions via HTTPException** — custom helpers in `app/core/exceptions.py`.
9. **Pydantic mandatory** — all endpoints return typed models. Never raw dicts.
10. **Async everywhere** — all I/O must be `async def`.

## Dependencies
```
fastapi>=0.111.0, uvicorn>=0.30.0
pydantic>=2.8.2, pydantic-settings>=2.3.4, pydantic[email]>=2.8.2
SQLAlchemy>=2.0.31, asyncpg>=0.29.0, psycopg[binary]>=3.2.1, alembic>=1.13.1
redis>=5.0.3, aiohttp>=3.9.0
```

## Phase 1 — PLAN
1. Understand the requirement. Ask clarifying questions.
2. Define contracts: request/response schemas, data shapes, validation rules
3. Identify layers: schemas, repository, service, router
4. Plan test scenarios: happy path, validation errors, auth errors, edge cases
5. Present the plan. Wait for confirmation.

## Phase 2 — RED (Tests)
1. Create unit test (mocked deps) for core logic
2. Create API test (httpx.AsyncClient + ASGITransport) for endpoint
3. Run tests — they MUST fail
4. If tests pass, revise. Never proceed to GREEN until tests fail.

## Phase 3 — GREEN (Implementation)
1. Create/update schemas in `app/schemas/<domain>/`
2. Create/update model + alembic migration
3. Create/update repository in `app/repositories/`
4. Create/update service in `app/services/<domain>/`
5. Create/update router in `app/api/v1/` + register in `__init__.py`
6. Run tests — they MUST pass

## Phase 4 — REFACTOR
1. Run linter (`ruff check app/`)
2. Check: N+1, missing indexes, async correctness, error handling
3. Verify all tests pass
4. Suggest command to run full test suite
