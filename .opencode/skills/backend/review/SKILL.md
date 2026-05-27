---
name: review
description: Use ONLY when reviewing code diffs, PRs, or staged changes. Read-only analysis. If reviewing Azure, security, or KQL code, also load the relevant domain skill. Trigger keywords: review, code review, PR review, check this code, audit, inspect.
---

# Review

## Core Rules
1. READ-ONLY. Review and suggest. Never modify files.
2. Focus on what matters: bugs and security first, then design, then style.
3. Be constructive. Suggest improvements, don't just criticize.
4. Use the project's existing patterns as the standard (not personal preference).

## What to Check

### Bugs & Correctness
- Off-by-one errors, inverted conditions, missing null checks
- Race conditions in async/concurrent code
- Incorrect assumptions about data shape or availability
- Edge cases not handled

### Security
- SQL injection, XSS, path traversal
- Missing auth checks on endpoints
- Secrets or credentials in code
- Unsafe deserialization

### Design & Architecture
- Does this fit the project's patterns and conventions?
- Is the right layer handling the right responsibility?
- Is this testable? Are there hidden dependencies?
- Will this scale? (query performance, memory usage)

### Error Handling
- Are exceptions caught and handled appropriately?
- Are error messages safe for the client (no stack traces)?
- Is there proper logging for debugging?

### Tests
- Do the tests actually verify the new behavior?
- Are edge cases and error paths covered?
- Are tests isolated and deterministic?

## Output Format
For each issue found:
1. Severity: CRITICAL / HIGH / MEDIUM / LOW
2. File and line reference
3. Description of the problem
4. Concrete suggestion for improvement
5. End with a summary: overall assessment, key risks, non-blocking suggestions
