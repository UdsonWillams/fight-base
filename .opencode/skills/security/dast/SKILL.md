---
name: dast
description: Dynamic security testing for running web apps using Python only. Probe endpoints, fuzz parameters, check headers, and detect common vulnerabilities (XSS, SQLi, misconfig) using requests/httpx. No external tools or services. Use when user says "DAST", "security scan", "fuzzing", "XSS test", "SQL injection test", "security headers check". Trigger: DAST, dynamic scan, security test, fuzz, probe, OWASP, header check, injection test.
license: MIT
metadata:
  author: awesome-ai-agent-skills
  version: 2.0.0
---

# Dynamic Application Security Testing — Python Native

Runtime security testing against running web apps using only Python libraries. Send crafted HTTP requests, fuzz input parameters, check response headers, and detect common vulnerabilities without external tools.

## Dependency Isolation (OPTIONAL)

Only install if performing a DAST scan. DAST tools must stay isolated from application dependencies.

```bash
# requirements-security.txt (create only if needed, add to .gitignore)
requests
httpx
beautifulsoup4
```

Or with `uv` / `pyproject.toml`:

```toml
[project.optional-dependencies]
security = [
    "requests",
    "httpx",
    "beautifulsoup4",
]
```

```bash
uv sync --group security  # only when scanning
# or
uv pip install -r requirements-security.txt  # only when scanning
```

## Workflow

1. **Define target** — Target URL, application type (web app, REST API, GraphQL), endpoints to test.
2. **Configure auth** — Bearer tokens, API keys, cookies, or form-based session tokens.
3. **Probe endpoints** — Send crafted payloads for XSS, SQLi, path traversal, SSRF, and header checks.
4. **Analyze responses** — Classify findings by vulnerability type, severity, confidence.
5. **Generate report** — Vulnerable URL, payload used, response evidence, severity, CWE, fix.

## Security Headers Check

```python
import requests

REQUIRED_HEADERS = {
    "Strict-Transport-Security": "Missing HSTS header",
    "X-Content-Type-Options": "Missing X-Content-Type-Options (MIME sniffing)",
    "X-Frame-Options": "Missing X-Frame-Options (clickjacking)",
    "Content-Security-Policy": "Missing CSP header",
    "X-XSS-Protection": "Missing X-XSS-Protection",
    "Referrer-Policy": "Missing Referrer-Policy",
}

MISCONFIGURED_HEADERS = {
    "Access-Control-Allow-Origin": lambda v: v == "*",
    "Server": lambda v: True,  # Leaks server info
    "X-Powered-By": lambda v: True,  # Leaks framework info
    "Set-Cookie": lambda v: "Secure" not in v,
    "Set-Cookie": lambda v: "HttpOnly" not in v,
}

def check_headers(url: str) -> dict:
    """Check response headers for security issues."""
    r = requests.get(url, timeout=10, allow_redirects=False)

    results = {"url": url, "status": r.status_code, "issues": []}

    # Check missing headers
    for header, message in REQUIRED_HEADERS.items():
        if header not in r.headers:
            results["issues"].append({
                "type": "missing-header",
                "severity": "medium",
                "header": header,
                "message": message,
                "cwe": "CWE-693",
            })

    # Check misconfigured headers
    for header, condition in MISCONFIGURED_HEADERS.items():
        if header in r.headers and condition(r.headers[header]):
            if header == "Access-Control-Allow-Origin" and r.headers[header] == "*":
                results["issues"].append({
                    "type": "misconfiguration",
                    "severity": "low",
                    "header": "Access-Control-Allow-Origin",
                    "value": "*",
                    "message": "CORS allows any origin",
                    "cwe": "CWE-942",
                })
            elif header == "Server":
                results["issues"].append({
                    "type": "information-leak",
                    "severity": "low",
                    "header": "Server",
                    "value": r.headers[header],
                    "message": "Server header leaks software version",
                    "cwe": "CWE-200",
                })
            elif header == "Set-Cookie" and "Secure" not in r.headers[header]:
                results["issues"].append({
                    "type": "misconfiguration",
                    "severity": "medium",
                    "header": "Set-Cookie",
                    "message": "Cookie missing Secure flag",
                    "cwe": "CWE-614",
                })

    return results
```

## SQL Injection Probing

```python
SQLI_PAYLOADS = [
    ("' OR '1'='1", "Tautology — returns all rows"),
    ("' OR '1'='1' --", "Tautology with comment"),
    ("admin'--", "Auth bypass — comment out password check"),
    ("' UNION SELECT NULL--", "UNION injection probe"),
    ("1; DROP TABLE users--", "Stacked query — destructive"),
    ("' OR 1=1 --", "Numeric tautology"),
]

def probe_sqli(url: str, params: list[str], method: str = "GET") -> list[dict]:
    """Test parameters for SQL injection vulnerability."""
    findings = []
    session = requests.Session()

    for param in params:
        for payload, description in SQLI_PAYLOADS:
            try:
                if method == "GET":
                    r = session.get(url, params={param: payload}, timeout=10)
                else:
                    r = session.post(url, json={param: payload}, timeout=10)

                text = r.text.lower()

                indicators = [
                    "sql syntax",
                    "mysql_fetch",
                    "ora-",
                    "postgresql",
                    "sqlite3",
                    "unclosed quotation mark",
                    "syntax error",
                    "division by zero",
                ]

                for indicator in indicators:
                    if indicator in text:
                        findings.append({
                            "type": "sqli",
                            "severity": "high",
                            "param": param,
                            "payload": payload,
                            "description": description,
                            "indicator": indicator,
                            "status": r.status_code,
                            "cwe": "CWE-89",
                        })
                        break
            except Exception:
                continue

    return findings
```

## XSS Probing

```python
XSS_PAYLOADS = [
    ("<script>alert(1)</script>", "Basic script tag"),
    ('"><script>alert(1)</script>', "Attribute breakout + script"),
    ("<img src=x onerror=alert(1)>", "Image onerror handler"),
    ("<svg onload=alert(1)>", "SVG onload handler"),
    ("javascript:alert(1)", "JavaScript protocol"),
]

def probe_xss(url: str, params: list[str], method: str = "GET") -> list[dict]:
    """Test parameters for reflected XSS."""
    findings = []
    session = requests.Session()

    for param in params:
        for payload, description in XSS_PAYLOADS:
            try:
                if method == "GET":
                    r = session.get(url, params={param: payload}, timeout=10)
                else:
                    r = session.post(url, json={param: payload}, timeout=10)

                text = r.text

                # Check if payload is reflected unescaped
                if payload in text:
                    # Verify it's not properly encoded
                    if payload not in text.replace("&lt;", "").replace("&gt;", "").replace("&quot;", ""):
                        continue  # Properly encoded — not vulnerable

                    findings.append({
                        "type": "xss",
                        "severity": "high",
                        "param": param,
                        "payload": payload,
                        "description": description,
                        "status": r.status_code,
                        "cwe": "CWE-79",
                    })
            except Exception:
                continue

    return findings
```

## Path Traversal Probing

```python
TRAVERSAL_PAYLOADS = [
    "../../../etc/passwd",
    "..%2F..%2F..%2Fetc%2Fpasswd",
    "....//....//....//etc/passwd",
    "..\\..\\..\\windows\\win.ini",
    "....\\\\....\\\\....\\\\windows\\\\win.ini",
]

TRAVERSAL_INDICATORS = [
    "root:x:0:",
    "[extensions]",
    "[fonts]",
    "No such file",
    "cannot open",
]

def probe_path_traversal(base_url: str, params: list[str]) -> list[dict]:
    """Test parameters for path traversal vulnerability."""
    findings = []
    session = requests.Session()

    for param in params:
        for payload in TRAVERSAL_PAYLOADS:
            try:
                r = session.get(f"{base_url}?", params={param: payload}, timeout=10)

                for indicator in TRAVERSAL_INDICATORS:
                    if indicator in r.text:
                        findings.append({
                            "type": "path-traversal",
                            "severity": "high",
                            "param": param,
                            "payload": payload,
                            "indicator": indicator,
                            "cwe": "CWE-22",
                        })
                        break
            except Exception:
                continue

    return findings
```

## SSRF Probing

```python
SSRF_PAYLOADS = [
    "http://169.254.169.254/latest/meta-data/",   # AWS metadata
    "http://metadata.google.internal/",              # GCP metadata
    "http://127.0.0.1:22",                          # Local SSH
    "http://localhost:8000/admin",                   # Local admin
    "file:///etc/passwd",                            # Local file
]

SSRF_INDICATORS = [
    "ami-id",
    "instance-id",
    "security-credentials",
]

def probe_ssrf(url: str, params: list[str], method: str = "GET") -> list[dict]:
    """Test parameters for SSRF vulnerability."""
    findings = []
    session = requests.Session()

    for param in params:
        for payload in SSRF_PAYLOADS:
            try:
                if method == "GET":
                    r = session.get(url, params={param: payload}, timeout=10)
                else:
                    r = session.post(url, json={param: payload}, timeout=10)

                for indicator in SSRF_INDICATORS:
                    if indicator.lower() in r.text.lower():
                        findings.append({
                            "type": "ssrf",
                            "severity": "high",
                            "param": param,
                            "payload": payload,
                            "indicator": indicator,
                            "cwe": "CWE-918",
                        })
                        break
            except Exception:
                continue

    return findings
```

## Open Endpoint Discovery

```python
COMMON_PROBES = [
    ("/.env", "Environment file", "high"),
    ("/.git/config", "Git repository exposed", "high"),
    ("/admin", "Admin panel exposed", "medium"),
    ("/api", "API root", "info"),
    ("/docs", "Swagger docs (FastAPI)", "low"),
    ("/redoc", "ReDoc docs (FastAPI)", "low"),
    ("/openapi.json", "OpenAPI spec exposed", "low"),
    ("/actuator", "Spring actuator exposed", "high"),
    ("/actuator/env", "Spring env exposed", "critical"),
    ("/debug", "Debug endpoint exposed", "high"),
    ("/phpinfo.php", "PHP info exposed", "high"),
    ("/robots.txt", "Robots file", "info"),
    ("/sitemap.xml", "Sitemap file", "info"),
    ("/wp-admin", "WordPress admin", "high"),
    ("/graphql", "GraphQL endpoint", "info"),
    ("/backup", "Backup directory", "high"),
    ("/log", "Log files exposed", "medium"),
    ("/console", "Web console exposed", "high"),
]

def discover_endpoints(base_url: str) -> list[dict]:
    """Discover open endpoints and sensitive files."""
    findings = []

    for path, description, severity in COMMON_PROBES:
        url = f"{base_url.rstrip('/')}{path}"
        try:
            r = requests.get(url, timeout=5, allow_redirects=False)

            if r.status_code in (200, 301, 302, 403):
                findings.append({
                    "type": "exposed-endpoint",
                    "severity": severity,
                    "url": url,
                    "status": r.status_code,
                    "description": description,
                    "cwe": "CWE-200" if severity != "info" else None,
                })
        except Exception:
            continue

    return findings
```

## Full Scan Orchestrator

```python
import json
from dataclasses import dataclass, field

@dataclass
class DastReport:
    target: str
    headers: list[dict] = field(default_factory=list)
    exposed_endpoints: list[dict] = field(default_factory=list)
    sqli: list[dict] = field(default_factory=list)
    xss: list[dict] = field(default_factory=list)
    traversal: list[dict] = field(default_factory=list)
    ssrf: list[dict] = field(default_factory=list)

    def critical(self) -> list[dict]:
        return [f for f in self.all() if f["severity"] == "critical"]

    def high(self) -> list[dict]:
        return [f for f in self.all() if f["severity"] == "high"]

    def all(self) -> list[dict]:
        return self.headers + self.exposed_endpoints + self.sqli + self.xss + self.traversal + self.ssrf

    def summary(self) -> str:
        lines = [f"DAST Report: {self.target}", "=" * 50]
        for sev in ("critical", "high", "medium", "low", "info"):
            items = [f for f in self.all() if f["severity"] == sev]
            if items:
                lines.append(f"\n{sev.upper()} ({len(items)}):")
                for item in items:
                    cwe = item.get("cwe", "")
                    lines.append(f"  [{item['type']}] {item.get('url', item.get('param', ''))} — {item.get('description', item.get('message', ''))} {cwe}")
        return "\n".join(lines)

def run_dast(base_url: str, params: list[str], auth_token: str | None = None) -> DastReport:
    """Run full DAST scan against target."""
    session = requests.Session()
    if auth_token:
        session.headers["Authorization"] = f"Bearer {auth_token}"
    # Mount session for all probe functions (pass as kwarg in prod)
    # Simplified: use session directly in each probe
    report = DastReport(target=base_url)
    report.headers = check_headers(base_url)
    report.exposed_endpoints = discover_endpoints(base_url)
    report.sqli = probe_sqli(base_url, params)
    report.xss = probe_xss(base_url, params)
    report.traversal = probe_path_traversal(base_url, params)
    report.ssrf = probe_ssrf(base_url, params)
    return report

# Usage
if __name__ == "__main__":
    report = run_dast(
        "https://staging.example.com",
        params=["q", "search", "id", "page", "sort", "filter"],
        auth_token="your-jwt-token",
    )
    print(report.summary())

    with open("dast-report.json", "w") as f:
        json.dump(report.all(), f, indent=2)
```

## Report Format

```json
{
  "type": "sqli",
  "severity": "high",
  "param": "search",
  "payload": "' OR '1'='1",
  "description": "Tautology — returns all rows",
  "indicator": "sql syntax",
  "status": 200,
  "cwe": "CWE-89"
}
```

## FastAPI-Specific Checks

```python
def check_fastapi_security(base_url: str) -> list[dict]:
    """FastAPI-specific security checks."""
    findings = []

    # Check if OpenAPI spec is public
    for path in ["/openapi.json", "/docs", "/redoc"]:
        try:
            r = requests.get(f"{base_url}{path}", timeout=5)
            if r.status_code == 200:
                findings.append({
                    "type": "fastapi-docs-exposed",
                    "severity": "low",
                    "url": f"{base_url}{path}",
                    "message": f"FastAPI {path} is publicly accessible in production",
                    "fix": "Set openapi_url=None and docs_url=None in FastAPI() constructor for production",
                    "cwe": "CWE-200",
                })
        except Exception:
            continue

    return findings

# Usage: combine with run_dast
report = run_dast("https://staging.example.com", ["q", "id", "page"])
report.exposed_endpoints.extend(check_fastapi_security("https://staging.example.com"))
```

## Best Practices

- **Run against staging, never production** — injection payloads can corrupt data or trigger side effects.
- **Use auth tokens** — most endpoints hide behind login. Always authenticate to reach the full surface area.
- **Start with passive checks first** — headers and endpoint discovery before active fuzzing.
- **Respect rate limits** — add `time.sleep(0.5)` between probes to avoid overwhelming the server.
- **Review findings manually** — automated probes produce false positives. Verify each finding before reporting.
- **Pair with SAST** — DAST finds runtime issues; SAST catches code-level flaws. Use both.
- **Filter out safe reflected XSS** — if the payload is HTML-encoded in the response (`&lt;script&gt;`), it's not vulnerable.

## Edge Cases

- **CSRF tokens** — forms with dynamic CSRF tokens need the token extracted from the page before POST. Use BeautifulSoup (`pip install beautifulsoup4`) to parse and re-submit.
- **Rate-limited APIs** — if the server returns 429, add exponential backoff: `time.sleep(2 ** attempt)`.
- **WAF blocking payloads** — a WAF may block probes. Test with benign payloads first to detect WAF presence, then adjust payloads.
- **JSON-only APIs** — use `Content-Type: application/json` with JSON-encoded payloads, not form-encoded.
