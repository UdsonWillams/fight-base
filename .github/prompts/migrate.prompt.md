---
description: "Create database migrations with automatic SQL review"
argument-hint: "[describe the schema change]"
---

You are creating a database migration. Follow these rules.

## Core Rules
1. Detect model/schema changes before generating migrations.
2. Always review the generated SQL before finalizing.
3. Warn about edge cases that autogenerate misses.
4. Never run migrations against production without explicit approval.

## Workflow
1. Detect changes by comparing models/schemas against database state
2. Generate migration (e.g., `alembic revision --autogenerate -m "description"`)
3. Review the generated migration file and SQL carefully
4. Warn about edge cases autogenerate commonly misses:
   - Nullable to non-nullable (needs default)
   - Renamed columns (detected as drop + add)
   - Custom constraints or indexes
   - Enum type changes
   - Data type changes that may cause data loss
5. Suggest the exact command to apply
6. Suggest the rollback command

## Safety Checklist
- Needs default for existing rows?
- Will this lock the table?
- Is the downgrade path defined?
- Are there dependent views/triggers?
