---
name: seed
description: Use ONLY when generating seed data scripts for populating the dev database with realistic fake data. If seeding data for Azure services, also load the relevant domain skill. Trigger keywords: seed, seed data, fake data, populate, fixtures, sample data, dev database.
---

# Seed

## Core Rules
1. Generate scripts in scripts/ (or the project's equivalent). Never modify application code.
2. Create realistic data — not just "test", "foo", "bar".
3. Make scripts idempotent (safe to run multiple times).
4. Include clear instructions on how to run the script.

## Workflow
1. **Identify** all models/entities that need seed data
2. **Determine** dependencies (e.g., users before orders, categories before products)
3. **Generate** a seed script that:
   - Creates data in dependency order
   - Uses realistic names, values, and relationships
   - Generates varied data (different statuses, roles, types)
   - Is idempotent (truncates or upserts)
4. **Create** a main entry point script (e.g., `scripts/seed_all.py`) if there are multiple
5. **Document** exactly how to run: `python scripts/seed_all.py`

## Data Quality
- Use realistic names (not "John Doe" for everything)
- Vary states: mix of active/inactive, different statuses, different roles
- Create meaningful relationships between entities
- Enough volume to test pagination, filtering, and edge cases
- Use deterministic but varied data (faker library if available, otherwise hardcoded arrays)

## Script Template Pattern
```python
"""Seed script for <entity>. Run with: python scripts/seed_<entity>.py"""
# 1. Imports (models, DB connection, faker if available)
# 2. Seed data arrays or generation logic
# 3. Upsert/insert logic
# 4. Main function with if __name__ == "__main__"
```
