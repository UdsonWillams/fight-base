---
name: feature
description: Use ONLY when implementing a new feature end-to-end. Follows strict TDD: test first, then code, then refactor. If feature involves Azure, security, or KQL, also load domain skills. Trigger keywords: feature, implement, create endpoint, new module, add functionality.
---

# Feature

## Core Rules
1. TDD is mandatory. Write tests BEFORE implementation. No exceptions.
2. Never skip the red-green-refactor cycle.
3. Tests MUST fail before implementation starts. If they pass immediately, the test is wrong — revise it.
4. Only proceed to the next phase when the current phase is complete.
5. If the feature involves external services (Azure, security, KQL, messaging, storage), also load the relevant domain skill alongside this skill.

## Architecture Standards

### Directory Structure

```
app/
├── api/
│   └── v1/
│       ├── __init__.py          # router aggregation
│       ├── users.py             # /users endpoints
│       ├── users/
│       │   ├── profiles.py      # /users/profiles subdomain
│       │   └── settings.py      # /users/settings subdomain
│       ├── auth.py
│       └── fighters.py
├── services/
│   ├── auth/
│   │   └── auth_service.py
│   ├── users/
│   │   └── user_service.py
│   └── fighters/
│       └── fighter_service.py
├── repositories/
│   ├── user_repository.py
│   └── fighter_repository.py
├── schemas/
│   ├── users/
│   │   ├── requests.py          # UserCreate, UserUpdate
│   │   └── responses.py         # UserResponse, UserListResponse
│   └── fighters/
│       ├── requests.py
│       └── responses.py
├── core/
│   ├── config.py                # Settings via pydantic-settings
│   ├── logger.py
│   ├── exceptions.py            # Custom HTTP exceptions
│   └── security.py              # JWT, password hashing
└── main.py
```

### View Layer (Router) — Keep Simple

```python
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Body
from app.schemas.users.requests import UserCreate
from app.schemas.users.responses import UserResponse
from app.services.users.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    data: UserCreate = Body(...),
    service: UserService = Depends(),
) -> UserResponse:
    return await service.create(data)

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int = Path(..., gt=0),
    service: UserService = Depends(),
) -> UserResponse:
    user = await service.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

@router.get("/", response_model=list[UserResponse])
async def list_users(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    service: UserService = Depends(),
) -> list[UserResponse]:
    return await service.list_paginated(page=page, size=size)
```

### Flow: View → Service → Repository

Every DB operation follows this chain. Views never call repositories directly.

### Pydantic Schemas

Separate per domain, split into `requests.py` and `responses.py`:

```python
# app/schemas/users/requests.py
from pydantic import BaseModel, Field, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)

class UserUpdate(BaseModel):
    email: EmailStr | None = Field(None, min_length=5, max_length=255)
    password: str | None = Field(None, min_length=8, max_length=128)
```

```python
# app/schemas/users/responses.py
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    id: int
    email: str
    is_active: bool
    created_at: datetime
```

### Exceptions

Use FastAPI's `HTTPException` for all errors. Define custom handlers in `app/core/exceptions.py` if needed.

```python
from fastapi import HTTPException, status

# 404 reusable
def user_not_found(user_id: int) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"User {user_id} not found",
    )
```

## Dependencies

```
fastapi>=0.111.0
uvicorn>=0.30.0
pydantic>=2.8.2
pydantic-settings>=2.3.4
pydantic[email]>=2.8.2
aiohttp>=3.9.0
redis>=5.0.3
SQLAlchemy>=2.0.31
asyncpg>=0.29.0
psycopg[binary]>=3.2.1
alembic>=1.13.1
```

## Workflow

### Phase 1 — PLAN
1. Understand the requirement fully. Ask clarifying questions if needed.
2. Define contracts: request/response schemas, data shapes, validation rules
3. Identify affected layers: schemas, repository, service, router
4. Plan test scenarios: happy path, validation errors, auth errors, edge cases
5. Present the plan to the user. Wait for confirmation before proceeding.

### Phase 2 — RED (Tests)
1. Create unit test for the core business logic (mocked dependencies)
2. Create API test for the endpoint (httpx.AsyncClient + ASGITransport)
3. Run the tests → they MUST fail
4. If tests pass, the new behavior isn't being tested. Revise the test.
5. Never proceed to GREEN until tests fail convincingly.

### Phase 3 — GREEN (Implementation)
1. Create or update Pydantic schemas in `app/schemas/<domain>/`
2. Create or update SQLAlchemy model and Alembic migration
3. Create or update repository in `app/repositories/`
4. Create or update service in `app/services/<domain>/`
5. Create or update router in `app/api/v1/` and register in `__init__.py`
6. Run the tests → they MUST pass

### Phase 4 — REFACTOR
1. Run linter/formatter (`ruff check app/`)
2. Check for: N+1 queries, missing DB indexes, async/await correctness, proper error handling
3. Verify all tests still pass (both new and existing)
4. Suggest the exact command to run the full test suite
