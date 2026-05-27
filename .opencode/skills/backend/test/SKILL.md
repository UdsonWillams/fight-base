---
name: test
description: Use ONLY when creating, modifying, or expanding tests. Do NOT use for application code changes. If testing Azure, security, or KQL code, also load the relevant domain skill. Trigger keywords: test, tests, testing, unit test, api test, coverage.
---

# Test

## Core Rules
1. Only edit test files. NEVER modify application code.
2. If a test reveals a bug, REPORT it clearly. Do NOT fix it yourself.
3. **pytest only.** Never use Python's built-in `unittest`. No `TestCase`, no `self.assert*`.
4. **Functions only.** No test classes. Every test is a plain `async def` function.
5. **Two test types only:**
   - **Unit tests** (`tests/unit/`) — isolated, fast. Mock ALL external dependencies (DB, HTTP, Redis, Azure, filesystem). Use `pytest-mock`.
   - **API tests** (`tests/api/`) — hit real endpoints via `httpx.AsyncClient` + `ASGITransport`. No mocks except external services.
6. Follow existing project patterns: fixtures in `conftest.py`, factories in `tests/fixtures/`.

## Dependencies

```
# requirements-dev.txt or [project.optional-dependencies] dev
pytest>=8.3.3
pytest-mock>=3.14.0
pytest-asyncio>=0.24.0
pytest-cov>=5.0.0
pytest-postgresql>=6.0.1
httpx>=0.27.0
```

## Docstring Pattern (Mandatory)

Every test function MUST have a docstring following Gherkin Given/When/Then:

```python
async def test_create_user_with_valid_data_returns_201(
    client: AsyncClient,
    db_session: AsyncSession,
):
    """
    Given a valid user payload with email and password
    When POST /api/v1/users is called
    Then return 201 with the created user response containing an id.
    """
    payload = {"email": "test@example.com", "password": "Secret123!"}
    response = await client.post("/api/v1/users", json=payload)
    assert response.status_code == 201
    body = response.json()
    assert "id" in body
    assert body["email"] == "test@example.com"
    assert "password" not in body
```

## Unit Test Pattern

```python
from pytest_mock import MockerFixture

async def test_get_user_by_id_returns_user_when_found(
    mocker: MockerFixture,
):
    """
    Given a user ID that exists in the database
    When UserService.get_by_id is called
    Then return the matching User schema.
    """
    mock_repo = mocker.AsyncMock()
    mock_repo.get_by_id.return_value = User(id=1, email="a@b.com")

    service = UserService(repository=mock_repo)
    result = await service.get_by_id(user_id=1)

    assert result is not None
    assert result.id == 1
    assert result.email == "a@b.com"
    mock_repo.get_by_id.assert_awaited_once_with(1)
```

## API Test Pattern

```python
from httpx import AsyncClient

async def test_get_user_by_id_returns_200_when_authenticated(
    client: AsyncClient,
    auth_headers: dict[str, str],
):
    """
    Given an authenticated user and an existing user ID 1
    When GET /api/v1/users/1 is called
    Then return 200 with the user data.
    """
    response = await client.get("/api/v1/users/1", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == 1
```

## Test Naming Convention

```
test_<action>_<scenario>_<expected_result>

Examples:
  test_create_user_with_valid_data_returns_201
  test_get_user_with_invalid_id_returns_404
  test_delete_own_account_returns_204
  test_login_with_expired_token_returns_401
```

## What to Test

- Happy path (expected input → expected output)
- Validation errors (missing fields, invalid types, out of range)
- Auth errors (no token, expired token, wrong role)
- Not found (valid ID format but doesn't exist)
- Edge cases (empty strings, max lengths, boundary values, nulls)
- State changes (DB mutations, cache invalidation, side effects)
- Concurrency (if applicable — race conditions, duplicate prevention)

## Commands

```bash
pytest tests/unit/test_user_service.py -v
pytest tests/api/test_users.py -v
pytest --cov=app --cov-report=term-missing
pytest -k "test_create_user" -v
```
