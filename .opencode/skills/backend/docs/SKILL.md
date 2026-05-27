---
name: docs
description: Use ONLY when generating or updating documentation: docstrings, OpenAPI/Swagger descriptions, API docs, module READMEs. If documenting Azure, security, or KQL modules, also load the relevant domain skill. Trigger keywords: docs, documentation, docstring, OpenAPI, swagger, README, document.
---

# Docs

## Core Rules
1. Generate documentation only. Do not modify application logic.
2. Match the project's existing docstring style (Google, NumPy, Sphinx, etc).
3. Keep descriptions clear, concise, and technically accurate.
4. Include parameter types, return types, and raised exceptions where applicable.

## Workflow
1. **Identify** the module, function, class, or endpoint to document
2. **Check** existing documentation style in the project (look at other docstrings)
3. **Generate** the documentation following the project's conventions
4. **Suggest** the exact file and line where the documentation was added

## What to Document
- **Functions/Methods**: description, args, returns, raises
- **Classes**: purpose, attributes, key methods
- **API Endpoints**: summary, parameters, request body, response schema, status codes
- **Modules**: purpose, key components, dependencies

## OpenAPI / API Docs
- Use the framework's native decorators (e.g., FastAPI summary/description params)
- Include response model, status codes, and example responses
- Document authentication requirements
