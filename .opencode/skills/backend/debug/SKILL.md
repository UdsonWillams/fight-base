---
name: debug
description: Use ONLY when investigating and fixing bugs. Reproduces first, confirms root cause, asks for approval before applying fixes. If bug involves Azure, security, or KQL, also load the relevant domain skill. Trigger keywords: debug, bug, error, fix, crash, 500, exception, traceback, not working, broken.
---

# Debug

## Core Rules
1. REPRODUCE the bug first. You must confirm you can see the error yourself.
2. IDENTIFY the root cause with concrete evidence (stack trace, variable values, logs).
3. ASK the user for confirmation before applying any fix. Do NOT fix silently.
4. Write a failing test that reproduces the bug before applying the fix.
5. After fixing, verify the test passes AND run the existing test suite.

## Workflow

### Step 1 — REPRODUCE
1. Understand the reported error: what was the input, what was expected, what happened
2. Reproduce the bug yourself — run the failing code, endpoint, or test
3. Capture the exact error message, stack trace, and context
4. If you cannot reproduce, ask the user for more details

### Step 2 — IDENTIFY
1. Trace the error to its root cause, not just the symptom
2. Check: recent changes, edge cases in the input, concurrency issues, environmental factors
3. Document: which file, which line, what condition triggers it, why it happens
4. Present your diagnosis to the user. Explain the cause in plain language.

### Step 3 — CONFIRM
1. Tell the user what the fix will be and where
2. WAIT for explicit approval before touching any file
3. Do not proceed without user confirmation

### Step 4 — FIX (test-first)
1. Write a test that reproduces the bug
2. Confirm the new test fails
3. Apply the fix to the application code
4. Confirm the new test passes
5. Run the existing test suite to catch regressions
6. Report: what was changed, which files, and the test command to verify
