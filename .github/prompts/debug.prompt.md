---
description: "Investigate and fix bugs with test-first approach"
argument-hint: "[describe the bug: error message, endpoint, expected vs actual]"
---

You are debugging a bug. Follow these rules strictly.

## Core Rules
1. REPRODUCE the bug first. Confirm you can see the error yourself.
2. IDENTIFY the root cause with concrete evidence.
3. ASK for confirmation before applying any fix. Do NOT fix silently.
4. Write a failing test that reproduces the bug before fixing.
5. After fixing, verify the test passes AND run existing tests.

## Step 1 — REPRODUCE
1. Understand the reported error: input, expected, actual
2. Reproduce the bug yourself
3. Capture exact error message, stack trace, context
4. If unable to reproduce, ask for more details

## Step 2 — IDENTIFY
1. Trace error to root cause, not just symptom
2. Check: recent changes, edge cases, concurrency, environment
3. Document: file, line, condition, why it happens
4. Present diagnosis in plain language

## Step 3 — CONFIRM
1. Tell the user what the fix will be and where
2. WAIT for explicit approval before touching any file

## Step 4 — FIX (test-first)
1. Write a test that reproduces the bug
2. Confirm the new test fails
3. Apply the fix
4. Confirm the new test passes
5. Run existing tests to catch regressions
6. Report: what changed, which files, test command to verify
