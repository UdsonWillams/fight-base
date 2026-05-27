---
description: Create or modify tests with pytest (unit with mocks, API with httpx). Functions only, Gherkin docstrings, never application code.
agent: tester
---

$ARGUMENTS

Load the test skill and follow it strictly: pytest only, functions only, Given/When/Then docstrings, never modify application code. If testing Azure, security, or KQL code, also load the relevant domain skill.
