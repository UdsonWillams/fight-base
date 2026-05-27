---
description: "Dynamic security testing for running web apps using Python-only probes"
argument-hint: "[target URL and what to test]"
---

You are running dynamic security testing against a live web application. Follow these rules.

## Dependency Isolation (OPTIONAL)
Only install if performing a scan. Create a dedicated file, don't mix with app deps:

```bash
# requirements-security.txt (create only when scanning, add to .gitignore)
requests
httpx
```

```bash
uv pip install -r requirements-security.txt  # only when scanning
```

## Core Rules
1. Run against STAGING only, never production.
2. Start passive (headers, endpoint discovery) before active fuzzing.
3. Always authenticate to reach protected endpoints.
4. Respect rate limits — add `time.sleep(0.5)` between probes.
5. Verify findings manually before reporting as vulnerabilities.

## Checks to Perform

### Security Headers
Check for: `Strict-Transport-Security`, `X-Content-Type-Options`, `X-Frame-Options`, `Content-Security-Policy`, `Referrer-Policy`. Flag missing or misconfigured.

### SQL Injection Probe
Send payloads: `' OR '1'='1`, `' OR '1'='1' --`, `admin'--`, `' UNION SELECT NULL--`. Check response for SQL error indicators: `sql syntax`, `mysql_fetch`, `ORA-`, `PostgreSQL`, `sqlite3`.

### XSS Probe
Send: `<script>alert(1)</script>`, `"><script>alert(1)</script>`, `<img src=x onerror=alert(1)>`, `<svg onload=alert(1)>`. If payload reflected unencoded → vulnerable.

### Path Traversal Probe
Send: `../../../etc/passwd`, `..%2F..%2F..%2Fetc%2Fpasswd`. Check response for file content indicators.

### SSRF Probe
Send: `http://169.254.169.254/latest/meta-data/`, `http://metadata.google.internal/`, `http://127.0.0.1:22`. Check for cloud metadata or internal response.

### Exposed Endpoints
Probe: `/.env`, `/.git/config`, `/admin`, `/docs`, `/redoc`, `/openapi.json`, `/debug`, `/actuator`, `/graphql`, `/backup`.

## Report Format
Findings sorted by severity (critical > high > medium > low > info). Each finding: type, URL, payload, response evidence, CWE, OWASP category, fix guidance.

```json
{"type": "sqli", "severity": "high", "param": "search", "payload": "' OR '1'='1", "indicator": "sql syntax", "cwe": "CWE-89"}
```
