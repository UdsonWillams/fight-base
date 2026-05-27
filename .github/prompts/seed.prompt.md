---
description: "Generate seed data scripts for populating the dev database with realistic fake data"
argument-hint: "[describe what data you need seeded]"
---

You are generating seed data scripts. Follow these rules.

## Core Rules
1. Generate scripts in scripts/ (or project equivalent). Never modify application code.
2. Create realistic data — not "test", "foo", "bar".
3. Make scripts idempotent (safe to run multiple times).
4. Include clear instructions on how to run.

## Workflow
1. Identify all models/entities that need seed data
2. Determine dependencies (e.g., users before orders)
3. Generate seed script that:
   - Creates data in dependency order
   - Uses realistic names, values, relationships
   - Generates varied data (different statuses, roles, types)
   - Is idempotent (truncates or upserts)
4. Create main entry point (e.g., `scripts/seed_all.py`) if multiple scripts
5. Document: `python scripts/seed_all.py`

## Data Quality
- Realistic names (not "John Doe" for everything)
- Mix of states: active/inactive, different statuses, roles
- Meaningful relationships between entities
- Enough volume for pagination, filtering, edge cases
- Deterministic but varied (faker library if available)

## Script Template
```python
"""Seed script for <entity>. Run: python scripts/seed_<entity>.py"""
# Imports (models, DB connection, faker if available)
# Seed data arrays or generation logic
# Upsert/insert logic
# Main function with if __name__ == "__main__"
```
