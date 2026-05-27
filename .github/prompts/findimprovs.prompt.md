---
description: "Analyze code for performance, security, and code quality improvements"
argument-hint: "[file, module, or area to analyze]"
---

You are analyzing code for improvements. Read-only. Follow these rules.

## Core Rules
1. READ-ONLY. Analyze and suggest. Never modify files.
2. Be specific: file, line, concrete suggestion.
3. Prioritize: security > correctness > performance > readability.

## What to Check

### Performance
- N+1 queries (eager loading needed?)
- Missing database indexes on filtered/sorted columns
- Unnecessary data loading
- Inefficient loops (batch, stream, query directly?)
- Caching opportunities

### Security
- SQL injection via raw queries or string interpolation
- Missing input validation
- Authentication/authorization gaps
- Exposed sensitive data in responses
- Insecure defaults

### Code Quality
- Duplicated logic
- Overly complex functions
- Missing error handling
- Async/await correctness
- Type safety gaps

### Structure
- God modules/classes
- Circular imports or tight coupling
- Business logic in wrong layer
- Missing abstractions

## Output Format
For each finding: severity (HIGH/MEDIUM/LOW), file:line, problem, fix suggestion, why it matters.
