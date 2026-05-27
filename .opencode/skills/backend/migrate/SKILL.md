---
name: migrate
description: Use ONLY when creating database migrations. Handles autogenerate, SQL review, and edge-case detection. If migrating for Azure/security features, also load the relevant domain skill. Trigger keywords: migration, migrate, alembic, database schema, add column, alter table.
---

# Migrate

## Core Rules
1. Detect model/schema changes before generating migrations.
2. Always review the generated SQL before finalizing.
3. Warn about edge cases that autogenerate misses.
4. Never run migrations against production without explicit user approval.

## Workflow
1. **Detect** changes by comparing current models/schemas against the database state
2. **Generate** the migration using the project's migration tool (e.g., `alembic revision --autogenerate -m "description"`)
3. **Review** the generated migration file and SQL carefully
4. **Warn** about edge cases that autogenerate commonly misses:
   - Nullable → non-nullable changes (needs default)
   - Renamed columns (detected as drop + add, needs manual fix)
   - Custom constraints or indexes
   - Enum type changes
   - Data type changes that may cause data loss
5. **Suggest** the exact command to apply the migration (e.g., `alembic upgrade head`)
6. **Suggest** the rollback command (`alembic downgrade -1`)

## Migration Safety Checklist
- Does this migration require a default value for existing rows?
- Will this migration lock the table?
- Is the downgrade path defined?
- Are there dependent views or triggers?
