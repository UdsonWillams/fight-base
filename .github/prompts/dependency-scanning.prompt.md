---
description: "Scan Python dependencies for known vulnerabilities, generate SBOMs, and enforce license compliance"
argument-hint: "[path to project or requirements.txt]"
---

You are scanning Python project dependencies for security vulnerabilities. Follow these rules.

## Dependency Isolation (OPTIONAL)
Only install if performing a scan. Create a dedicated file, don't mix with app deps:

```bash
# requirements-security.txt (create only when scanning, add to .gitignore)
pip-audit
cyclonedx-py
pipdeptree
pip-licenses
```

```bash
uv pip install -r requirements-security.txt  # only when scanning
```

## Workflow
1. Detect manifest files: `requirements.txt`, `pyproject.toml`, `Pipfile.lock`, `poetry.lock`, `uv.lock`
2. Resolve full dependency tree including transitive deps with `pipdeptree --json-tree`
3. Scan: `pip-audit -r requirements.txt --format json --output audit.json`
4. License check: `pip-licenses --format json --output licenses.json`
5. Report: CVE IDs, CVSS scores, severity, affected versions, fixed versions, dependency paths
6. Fix: suggest minimum version bumps, generate updated manifest files

## Tools
| Tool | Command | Purpose |
|------|---------|---------|
| `pip-audit` | `pip-audit -r requirements.txt` | CVE scan via PyPI + OSV |
| `pip check` | `pip check` | Broken constraint detection |
| `pipdeptree` | `pipdeptree --json-tree` | Full dependency graph |
| `pip-licenses` | `pip-licenses --format json` | License audit |
| `cyclonedx-py` | `cyclonedx-py requirements -o sbom.json` | CycloneDX SBOM |

## Report Format
| # | Severity | Package | Installed | Fixed In | CVE | Dependency Path |
|---|----------|---------|-----------|----------|-----|-----------------|

## Best Practices
- Scan on every CI build
- Monitor transitive deps (80%+ of vulns come from them)
- Maintain a license allow-list (MIT, Apache-2.0, BSD)
- Generate SBOMs for every release
- Flag unmaintained packages (no commits in 12+ months)
