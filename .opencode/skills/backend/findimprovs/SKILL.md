---
name: findimprovs
description: Use ONLY when analyzing code for improvements. Read-only analysis of performance, security, patterns, and code quality. If analyzing Azure, security, or KQL code, also load the relevant domain skill. Trigger keywords: improve, improvements, analyze, performance, security audit, code quality, best practices.
---

# Find Improvements

## Core Rules
1. READ-ONLY. Analyze and suggest. Never modify files.
2. Be specific. Point to exact file, line, and suggest concrete changes.
3. Prioritize by impact: security > correctness > performance > readability.

## What to Check

### Performance
- N+1 queries (eager loading needed?)
- Missing database indexes on filtered/sorted columns
- Unnecessary data loading (load only needed fields)
- Inefficient loops (can it be batched, streamed, or queried directly?)
- Caching opportunities (repeated expensive operations)

### Security
- SQL injection via raw queries or string interpolation
- Missing input validation or sanitization
- Authentication/authorization gaps (missing guards on endpoints)
- Exposed sensitive data (passwords, tokens, internal errors in responses)
- Insecure defaults or configurations

### Code Quality
- Duplicated logic (extract to shared utility)
- Overly complex functions (break into smaller units)
- Missing error handling (unhandled exceptions, missing try/except)
- Async/await correctness (blocking calls in async context, missing awaits)
- Type safety (missing type hints, broad typing)

### Structure
- God modules / classes (too many responsibilities)
- Circular imports or tight coupling
- Business logic in wrong layer (e.g., in router instead of service)
- Missing abstractions where needed

## Output Format
For each finding, report:
1. Severity: HIGH / MEDIUM / LOW
2. File and line
3. Problem description
4. Concrete fix suggestion (code)
5. Why it matters
