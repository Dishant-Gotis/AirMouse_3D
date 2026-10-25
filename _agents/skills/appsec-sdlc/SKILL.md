---
skill_name: appsec-sdlc
description: Application security in SDLC including threat modeling, code review, DAST, and bug bounty
category: [security-advanced]
version: 1.0.0
---

# AppSec in SDLC

Integrating security throughout the software development lifecycle prevents vulnerabilities. Master threat modeling, secure code review, DAST, and vulnerability management.

## Threat Modeling

STRIDE methodology for identifying threats:
- **S**poofing: Identity spoofing
- **T**ampering: Data modification
- **R**epudiation: Denying actions
- **I**nformation Disclosure: Unauthorized access
- **D**enial of Service: Service unavailability
- **E**levation of Privilege: Unauthorized actions

```python
# Threat model example
threats = {
    'user_authentication': {
        'spoofing': [
            'Attacker impersonates legitimate user',
            'Mitigation: MFA, rate limiting'
        ],
        'tampering': [
            'Session token theft',
            'Mitigation: HTTPOnly cookies, CSRF tokens'
        ]
    },
    'api_endpoint': {
        'dos': [
            'Rate limiting bypass',
            'Mitigation: API throttling, WAF'
        ],
        'elevation': [
            'Privilege escalation via API',
            'Mitigation: Authorization checks, role-based access'
        ]
    }
}

def assess_threats():
    for component, threat_list in threats.items():
        for threat_type, details in threat_list.items():
            print(f"{component} - {threat_type}: {details}")
```

## Secure Code Review Checklist

```
OWASP Top 10 Checks:
- A01:2021 – Broken Access Control
- A02:2021 – Cryptographic Failures
- A03:2021 – Injection
- A04:2021 – Insecure Design
- A05:2021 – Security Misconfiguration
- A06:2021 – Vulnerable and Outdated Components
- A07:2021 – Identification and Authentication Failures
- A08:2021 – Software and Data Integrity Failures
- A09:2021 – Logging and Monitoring Failures
- A10:2021 – Server-Side Request Forgery

Code Review Items:
1. Input validation - sanitize all user input
2. Authentication - verify identity
3. Authorization - check permissions
4. Cryptography - use established libraries
5. Error handling - don't expose sensitive info
6. Logging - log security events
7. Dependency management - keep updated
8. Configuration - no hardcoded secrets
9. API design - least privilege
10. Testing - security test coverage
```

## DAST Tools and Automation

```bash
#!/bin/bash
# DAST pipeline

# OWASP ZAP scanning
docker run -v $(pwd):/zap/wrk:rw owasp/zap2docker-stable \
  -t http://target-app:8000 \
  -r zap-report.html

# SQLMap for SQL injection
python3 sqlmap.py \
  -u "http://target-app/search?q=test" \
  --dbs \
  --batch

# Burp Suite CLI scanning
burpsuite_community \
  --project-file=project.burp \
  --user-config-file=config.burp

# OWASP Dependency Check
dependency-check \
  --project "MyApp" \
  --scan ./src \
  --format HTML
```

## SAST Integration

```yaml
# GitHub Actions SAST workflow
name: SAST
on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      # Python security check
      - name: Bandit
        run: |
          pip install bandit
          bandit -r src/ -f json -o bandit-report.json

      # Dependency vulnerability check
      - name: Safety
        run: |
          pip install safety
          safety check --json > safety-report.json

      # Code quality + security
      - name: SonarQube
        uses: SonarSource/sonarcloud-github-action@master
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}

      # Secrets detection
      - name: TruffleHog
        run: |
          pip install truffleHog
          trufflehog git file://. --regex --json
```

## Security Testing Framework

```python
# security_tests.py
import pytest
import requests
from urllib.parse import urljoin

class SecurityTests:
    BASE_URL = "http://localhost:8000"

    def test_sql_injection(self):
        """Test SQL injection protection"""
        payload = "'; DROP TABLE users; --"
        response = requests.get(
            urljoin(self.BASE_URL, "/search"),
            params={"q": payload}
        )
        # Should not expose database errors
        assert "syntax error" not in response.text.lower()
        assert response.status_code != 500

    def test_xss_protection(self):
        """Test XSS protection"""
        payload = "<script>alert('XSS')</script>"
        response = requests.post(
            urljoin(self.BASE_URL, "/comment"),
            json={"content": payload}
        )
        # Should be escaped
        assert payload not in response.text
        assert "&lt;script&gt;" in response.text or "alert" not in response.json()

    def test_csrf_protection(self):
        """Test CSRF token validation"""
        # GET form
        resp1 = requests.get(urljoin(self.BASE_URL, "/form"))
        csrf_token = resp1.cookies.get('csrf_token')

        # POST without token
        resp2 = requests.post(
            urljoin(self.BASE_URL, "/form"),
            json={"data": "test"}
        )
        assert resp2.status_code == 403

        # POST with token
        resp3 = requests.post(
            urljoin(self.BASE_URL, "/form"),
            json={"data": "test", "csrf_token": csrf_token},
            cookies={"csrf_token": csrf_token}
        )
        assert resp3.status_code == 200

    def test_authentication_required(self):
        """Test authentication enforcement"""
        response = requests.get(
            urljoin(self.BASE_URL, "/dashboard"),
            allow_redirects=False
        )
        assert response.status_code == 302
        assert "login" in response.headers.get("Location", "").lower()

    def test_authorization_enforced(self):
        """Test authorization enforcement"""
        # Login as regular user
        auth_response = requests.post(
            urljoin(self.BASE_URL, "/login"),
            json={"username": "user", "password": "pass"}
        )

        # Try accessing admin endpoint
        headers = {
            "Authorization": f"Bearer {auth_response.json()['token']}"
        }
        response = requests.get(
            urljoin(self.BASE_URL, "/admin/users"),
            headers=headers
        )
        assert response.status_code == 403

    def test_rate_limiting(self):
        """Test rate limiting"""
        responses = []
        for i in range(100):
            resp = requests.get(urljoin(self.BASE_URL, "/api/data"))
            responses.append(resp.status_code)

        # Should eventually return 429 (Too Many Requests)
        assert 429 in responses

    def test_sensitive_data_exposure(self):
        """Test that sensitive data isn't exposed"""
        response = requests.get(urljoin(self.BASE_URL, "/api/user"))
        data = response.json()

        # Password should never be in response
        assert 'password' not in data
        assert 'password_hash' not in data
        assert 'credit_card' not in data
```

## Bug Bounty Program Setup

```markdown
# Bug Bounty Program Guidelines

## Scope
- Web application: https://app.example.com
- Mobile API: https://api.example.com
- NOT in scope: legacy.example.com, dev.example.com

## Rewards
- Critical (RCE, Auth Bypass): $5,000
- High (SQLi, XXE): $2,000
- Medium (XSS, CSRF): $500
- Low (Info Disclosure): $100

## Process
1. Report via HackerOne or security@example.com
2. Avoid public disclosure before fix
3. Give 90 days for patch before disclosure
4. Respect PII - don't exfiltrate data

## Out of Scope
- Social engineering
- Denial of Service
- Network issues
- Third-party vulnerabilities
```

## Best Practices

1. **Threat modeling**: Identify threats early
2. **Secure coding**: Follow OWASP guidelines
3. **Code review**: Peer review all code changes
4. **Static analysis**: Use SAST tools
5. **Dynamic testing**: Run DAST before release
6. **Dependency management**: Keep libraries updated
7. **Testing**: Include security test cases
8. **Monitoring**: Log and alert on suspicious activity
9. **Incident response**: Have documented procedures
10. **Training**: Educate developers on secure coding

## Key Takeaways

- Threat modeling identifies risks early
- Secure code review catches vulnerabilities
- DAST tools find runtime vulnerabilities
- SAST automates code vulnerability detection
- Bug bounty programs find real-world vulnerabilities
- Integration throughout SDLC prevents vulnerabilities
