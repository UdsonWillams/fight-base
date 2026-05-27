---
name: dependency-scanning
description: Scan Python project dependencies for known vulnerabilities, generate SBOMs, and enforce license compliance. Use when user says "scan dependencies", "audit packages", "dependency check", "pip-audit", "safety check", "vulnerability scan", "SBOM", or "license audit". Trigger keywords: dependency, dependencies, vulnerable, vulnerability, CVE, pip-audit, safety, SBOM, license, supply chain.
license: MIT
metadata:
  author: awesome-ai-agent-skills
  version: 1.0.0
---

# Dependency Scanning — Python

Analyze Python project dependencies (direct and transitive) for known security vulnerabilities, outdated packages, and license compliance. Query vulnerability databases (NVD, GitHub Advisory, OSV), produce structured reports with CVE identifiers and remediation guidance, and generate SBOM in standard formats.

## Workflow

1. **Detect manifest files** — Locate `requirements.txt`, `requirements-dev.txt`, `pyproject.toml`, `Pipfile`, `Pipfile.lock`, `poetry.lock`, or `uv.lock`. Detect monorepo structures with multiple manifests.

2. **Resolve full dependency tree** — Parse lock files to build complete dependency graph including transitive deps. Identify dependency depth, shared sub-dependencies, and version constraints. Flag phantom dependencies used in code but missing from the manifest.

3. **Scan against vulnerability databases** — Query NVD, GitHub Advisory, and OSV for each resolved package and version. Match by CPE or PURL. Record CVE IDs, CVSS scores, severity, affected version ranges, and fixed versions.

4. **Assess license compliance** — Extract declared license for each dependency. Compare against project license policy. Flag copyleft licenses (GPL, AGPL) in proprietary projects. Identify packages with no declared license. Detect license conflicts between direct and transitive deps.

5. **Generate SBOM and vulnerability report** — Produce SBOM in CycloneDX or SPDX format. Generate vulnerability report sorted by severity: CVE IDs, affected dependency paths, available fix versions, and whether the vulnerable code path is reachable.

6. **Recommend and apply fixes** — Suggest minimum version upgrades that resolve vulnerabilities without breaking changes. Generate updated manifest and lock files. Flag cases where no fix is available and suggest alternatives or workarounds.

## Dependency Isolation (OPTIONAL)

Only install if performing a dependency scan. Security tools must stay isolated from application dependencies.

```bash
# requirements-security.txt (create only if needed, add to .gitignore)
pip-audit
safety
cyclonedx-py
pipdeptree
pip-licenses
```

Or with `uv` / `pyproject.toml`:

```toml
[project.optional-dependencies]
security = [
    "pip-audit",
    "safety",
    "cyclonedx-py",
    "pipdeptree",
    "pip-licenses",
]
```

```bash
uv sync --group security  # only when scanning
# or
uv pip install -r requirements-security.txt  # only when scanning
```

## Scanning Tools

| Tool | Command | Best For |
|------|---------|----------|
| `pip-audit` | `pip-audit -r requirements.txt` | Vulnerability scan using PyPI + OSV |
| `safety` | `safety scan` | Commercial-grade CVE + policy enforcement |
| `pip check` | `pip check` | Dependency conflict detection |
| `pipdeptree` | `pipdeptree --json-tree` | Dependency tree visualization |
| `pip-licenses` | `pip-licenses --format json` | License audit and compliance |
| `cyclonedx-py` | `cyclonedx-py requirements requirements.txt` | SBOM generation (CycloneDX) |

## SBOM Formats

| Format | Tool | Command |
|--------|------|---------|
| CycloneDX JSON | `cyclonedx-py` | `cyclonedx-py requirements -o sbom.json` |
| CycloneDX XML | `cyclonedx-py` | `cyclonedx-py requirements -o sbom.xml --format xml` |
| SPDX JSON | `sbom4python` | `sbom4python -r requirements.txt -f spdx-json` |

## CI/CD Integration

### GitHub Actions

```yaml
- name: Dependency audit
  run: |
    pip install pip-audit
    pip-audit -r requirements.txt --format json --output audit.json
- name: Upload audit report
  uses: actions/upload-artifact@v4
  with:
    name: dependency-audit
    path: audit.json
```

### GitLab CI

```yaml
dependency-scan:
  image: python:3.12
  script:
    - pip install safety
    - safety scan -r requirements.txt --output json > safety-report.json
  artifacts:
    paths:
      - safety-report.json
```

## Example: Python Project Scan

### Step 1 — Detect and Audit

```bash
cd project/
pip-audit -r requirements.txt --format json --output audit.json
```

### Step 2 — Vulnerability Report

| # | Severity | Package | Installed | Fixed In | CVE | Description |
|---|----------|---------|-----------|----------|-----|-------------|
| 1 | Critical | `cryptography` | 38.0.0 | 41.0.6 | CVE-2023-49083 | NULL pointer dereference when loading PKCS7 certificates |
| 2 | High | `requests` | 2.28.0 | 2.31.0 | CVE-2023-32681 | Leaking Proxy-Authorization header to redirected hosts |
| 3 | High | `Jinja2` | 3.1.1 | 3.1.3 | CVE-2024-22195 | Cross-site scripting via xmlattr filter |
| 4 | Medium | `setuptools` | 65.0.0 | 70.0.0 | CVE-2024-6345 | Remote code execution via download functions |
| 5 | Medium | `urllib3` | 1.26.12 | 1.26.18 | CVE-2023-45803 | Request body not stripped after redirect |

### Step 3 — Auto-Fixed requirements.txt

```
cryptography>=41.0.6     # was 38.0.0 — fix: CVE-2023-49083
requests>=2.31.0         # was 2.28.0 — fix: CVE-2023-32681
Jinja2>=3.1.3            # was 3.1.1  — fix: CVE-2024-22195
setuptools>=70.0.0       # was 65.0.0 — fix: CVE-2024-6345
urllib3>=1.26.18         # was 1.26.12 — fix: CVE-2023-45803
Flask==3.0.0
gunicorn==21.2.0
```

### Step 4 — Dependency Tree

```bash
pipdeptree --json-tree > deps.json

# Example output (abbreviated):
# Flask==3.0.0
#   Jinja2==3.1.1               <-- vulnerable: CVE-2024-22195
#   MarkupSafe==2.1.3
#     (no known vulnerabilities)
#   Werkzeug==3.0.1
#   click==8.1.7
# gunicorn==21.2.0
# requests==2.28.0              <-- vulnerable: CVE-2023-32681
#   urllib3==1.26.12            <-- vulnerable: CVE-2023-45803
#   certifi==2023.7.22
#   idna==3.6
```

### Step 5 — License Check

```bash
pip-licenses --format json --output licenses.json

# Flag copyleft issues:
# GPL-3.0        some-internal-lib==1.2.3    ⚠️ BLOCKED in proprietary project
# LGPL-2.1       pylib==4.5.6                ⚠️ REVIEW required
# UNKNOWN        obscure-pkg==0.1.0           ⚠️ No license declared
```

## Common Python CVEs (2023-2024)

| Package | CVE | CVSS | Fixed In | Impact |
|---------|-----|------|----------|--------|
| `cryptography` | CVE-2023-49083 | 7.5 | 41.0.6 | PKCS7 certificate parsing |
| `requests` | CVE-2023-32681 | 6.1 | 2.31.0 | Proxy-Authorization leak |
| `Jinja2` | CVE-2024-22195 | 5.4 | 3.1.3 | XSS via xmlattr filter |
| `setuptools` | CVE-2024-6345 | 7.8 | 70.0.0 | RCE via download |
| `urllib3` | CVE-2023-45803 | 6.5 | 1.26.18 | Request body leak |
| `certifi` | CVE-2023-37920 | 7.5 | 2023.7.22 | Untrusted root cert removal |
| `aiohttp` | CVE-2024-23334 | 7.5 | 3.9.2 | Directory traversal |
| `idna` | CVE-2024-3651 | 7.5 | 3.7 | Internationalized domain spoofing |

## Best Practices

- **Scan on every CI build** — integrate `pip-audit` or `safety` into CI so new vulnerabilities are caught before merge, not after deploy.
- **Pin dependencies** — use `==` for exact versions in `requirements.txt` or `poetry.lock` / `uv.lock` for reproducible builds.
- **Monitor transitive deps** — over 80% of Python vulnerabilities come from transitive dependencies. Always resolve and scan the full tree.
- **Automate update PRs** — use Dependabot (GitHub) or Renovate to auto-open PRs when fix versions become available.
- **Maintain a license allow-list** — define approved licenses (MIT, Apache-2.0, BSD, ISC) and block builds introducing GPL/AGPL in proprietary projects.
- **Generate SBOMs for every release** — store CycloneDX or SPDX SBOMs alongside release artifacts for supply chain transparency and incident response.
- **Use `pip check` for conflicts** — run `pip check` to detect broken dependency constraints before they cause runtime errors.

## Edge Cases

- **Vulnerability with no fix available** — if CVE exists but no patched version is released, assess: is the vulnerable code path reachable? If yes, replace the dependency or apply a local patch. If the CVE is in an indirect dependency that your code never calls, it may be safe to ignore with documentation.
- **Monorepos with mixed manifests** — scan each `requirements.txt`, `pyproject.toml`, `Pipfile` independently. Produce a unified report that maps vulnerabilities to the service or module they affect.
- **Private PyPI registries** — packages from private registries (Azure Artifacts, AWS CodeArtifact) won't appear in public vulnerability databases. Maintain a private advisory feed or configure `pip-audit` with the `--index-url` flag to scan internal packages.
- **Version pinning conflicts** — upgrading a transitive dependency may break a direct dependency's version constraint. Use `pip check` after every automated fix to verify no conflicts were introduced.
- **Archived or unmaintained packages** — a package with no known CVEs but no active maintainer is still a supply chain risk. Flag unmaintained packages (no commits in 12+ months) and suggest migration to maintained alternatives.
- **Build-time vs runtime deps** — dev dependencies (linters, test frameworks, build tools) have different risk profiles than runtime deps. Separate scans for `requirements.txt` (runtime) and `requirements-dev.txt` (dev) with different severity thresholds — dev deps can tolerate medium sev, runtime deps should fail on medium+.
