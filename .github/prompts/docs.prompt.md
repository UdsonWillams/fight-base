---
description: "Generate docstrings, OpenAPI descriptions, and module documentation"
argument-hint: "[what do you want documented?]"
---

You are generating documentation. Follow these rules.

## Core Rules
1. Generate documentation only. Do not modify application logic.
2. Match the project's existing docstring style (Google, NumPy, Sphinx).
3. Keep descriptions clear, concise, and technically accurate.
4. Include parameter types, return types, and raised exceptions.

## Workflow
1. Identify the module, function, class, or endpoint to document
2. Check existing documentation style in the project
3. Generate documentation following conventions
4. Suggest the exact file and line

## What to Document
- Functions/Methods: description, args, returns, raises
- Classes: purpose, attributes, key methods
- API Endpoints: summary, parameters, request body, response schema, status codes
- Modules: purpose, key components, dependencies

## OpenAPI / API Docs
- Use the framework's native decorators (summary, description params)
- Include response model, status codes, example responses
- Document authentication requirements
