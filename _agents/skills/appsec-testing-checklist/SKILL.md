---
skill_name: appsec-testing-checklist
description: AppSec testing checklist - OWASP WSTG, test cases, tools, documentation, reporting
category: [security, advanced]
version: 1.0.0
---

# Application Security Testing Checklist

## OWASP Testing Guide (WSTG) Mapping

```
A1: Information Gathering
- [ ] Conduct search engine discovery (Google dorks)
- [ ] Identify web application technology stack
- [ ] Review robots.txt and sitemap.xml
- [ ] Enumerate subdomains and directories
- [ ] Identify comments in source code
- [ ] Check client-side dependencies (JS libraries)
Tools: Shodan, Wayback Machine, Wappalyzer, ffuf

A2: Configuration & Deployment Management
- [ ] Check for admin interfaces (.../admin, /wp-admin)
- [ ] Review default credentials (admin/admin)
- [ ] Check for backup files (.bak, .old, .~)
- [ ] Verify error message handling
- [ ] Check HTTPS enforcement
- [ ] Review security headers (CSP, X-Frame-Options)
Tools: Burp Suite, curl, grep

A3: Identity Management
- [ ] Test user enumeration
- [ ] Check password policy strength
- [ ] Test account lockout mechanisms
- [ ] Review session management
- [ ] Check for session fixation
- [ ] Verify MFA implementation
Tools: Burp Suite, custom scripts

A4: Authentication Testing
- [ ] Test password reset flow
- [ ] Check for credential storage in logs
- [ ] Review CAPTCHA bypasses
- [ ] Test default credentials
- [ ] Check for brute force protection
Tools: Hydra, John, password list

A5: Authorization Testing
- [ ] Test horizontal privilege escalation (IDOR)
- [ ] Test vertical privilege escalation
- [ ] Check authorization on all endpoints
- [ ] Test for forced browsing
- [ ] Verify function-level authorization
Tools: Burp Suite, custom repeater

A6: Session Management Testing
- [ ] Check token entropy
- [ ] Test token timeout
- [ ] Verify token invalidation on logout
- [ ] Check for HTTP cookies on HTTPS
- [ ] Test session fixation
Tools: Burp Suite, cookies analyzer

A7: Input Validation Testing
- [ ] SQL Injection
  - [ ] Authentication bypass
  - [ ] Data extraction
  - [ ] Blind SQLi with time-based
- [ ] Cross-Site Scripting (XSS)
  - [ ] Reflected XSS
  - [ ] Stored XSS
  - [ ] DOM-based XSS
- [ ] Command Injection
- [ ] LDAP Injection
- [ ] XML Injection / XXE
Tools: SQLmap, Burp Suite, XSStrike

A8: Business Logic Testing
- [ ] Test price manipulation
- [ ] Check quantity validation
- [ ] Test payment bypass
- [ ] Verify workflow sequence
- [ ] Check for race conditions
- [ ] Test multi-step process bypass
Tools: Burp Suite, custom logic testing

A9: API Testing
- [ ] Check API authentication
- [ ] Test rate limiting
- [ ] Verify API versioning security
- [ ] Check for excessive data exposure
- [ ] Test API error handling
- [ ] Verify pagination limits
Tools: Postman, curl, custom scripts

A10: Client-Side Testing
- [ ] Check for sensitive data in localStorage
- [ ] Review JavaScript for secrets
- [ ] Test DOM-based vulnerabilities
- [ ] Check client-side validation
- [ ] Review CORS configuration
- [ ] Test WebSocket security
Tools: Browser DevTools, Burp Suite

A11: CMS Testing
- [ ] Check for known CMS vulnerabilities
- [ ] Test plugin security
- [ ] Verify admin access controls
- [ ] Check default installations
Tools: WPScan (WordPress), vulnerability scanners
```

## Test Case Template

```javascript
// Test Case: SQL Injection in Login Form
TestCase: SQL-001
Title: SQL Injection in Login Form
Severity: CRITICAL
CWE: CWE-89

Precondition:
- Access login page
- Burp Suite intercepting traffic

Steps:
1. Enter username: admin' OR '1'='1' --
2. Enter password: anything
3. Click Login
4. Observe response in Burp

Expected Result:
- Authorization check fails (secure behavior)
- Error message does not expose database info

Actual Result:
- Login successful (VULNERABLE)
- User authenticated as admin

Evidence:
- Request: POST /login
  username=admin' OR '1'='1' --&password=anything
- Response: 200 OK, authenticated as admin

Mitigation:
- Use parameterized queries
- Example: PreparedStatement in Java
```

## Automated vs Manual Testing

```
Automation Tools (Fast, Many Tests):
- OWASP ZAP: Free, integrates with CI/CD
- Burp Suite Pro: Comprehensive scanner
- Nessus: Vulnerability scanner
- SQLmap: SQL injection detection
- NIKTO: Web server scanner

Manual Testing (Thorough, Business Logic):
- Burp Suite: Interactive testing
- Custom scripts: Application-specific tests
- Browser DevTools: Client-side inspection
- API testing tools: Postman, curl

Combination Strategy:
1. Automated scan (identify obvious issues)
2. Manual testing (business logic, bypass attempts)
3. Code review (vulnerabilities automation misses)
4. Retest (verify fixes)
```

## Test Coverage Matrix

```
Risk | Component | Test Type | Tool | Status
-----|-----------|-----------|------|-------
HIGH | Login | Auth bypass | Manual | PASS
HIGH | Login | SQL injection | SQLmap | FAIL -> PASS
HIGH | API | Auth bypass | Burp | PASS
CRIT | Upload | File type bypass | Manual | FAIL -> FIX
MED | Search | XSS | ZAP | PASS
MED | API | Rate limit | Manual | PASS
LOW | Contact | CSRF | Burp | PASS

Coverage: 7/7 tests = 100%
Critical Issues: 0
High Issues: 0 (1 fixed)
```

## Reporting

```markdown
# Application Security Test Report

## Executive Summary
- Test Date: 2024-03-15
- Scope: Web application v2.1.0
- Severity: CRITICAL (1), HIGH (3), MEDIUM (5)
- Recommendation: Fix critical issues before production

## Findings

### CRITICAL

**SQL Injection in Login Form**
- Location: POST /login
- Risk: Database breach, authentication bypass
- CVSS: 9.8
- Proof: admin' OR '1'='1' --
- Remediation: Use parameterized queries

### HIGH

[3 more findings...]

## Metrics
- Test cases executed: 50
- Pass rate: 92%
- Issues found: 9
- Critical items: 1

## Timeline
- Testing: 2024-03-10 to 2024-03-15
- Report: 2024-03-20
- Retesting: 2024-04-15
```

## Integration with CI/CD

```yaml
# GitHub Actions workflow
name: Security Tests

on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Run SAST
        run: |
          npm install -g snyk
          snyk test --severity-threshold=high

      - name: Run DAST (local)
        run: |
          npm install -g @owasp/zap
          zap-cli scan http://localhost:3000

      - name: Publish results
        if: always()
        uses: actions/upload-artifact@v2
        with:
          name: security-reports
          path: reports/

      - name: Comment on PR
        if: failure()
        uses: actions/github-script@v6
        with:
          script: |
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: 'Security tests failed. See attached reports.'
            })
```

## Key Takeaways

- **WSTG**: Use structured testing guide
- **Automation**: Handle volume, manual for logic
- **Checklists**: Ensures consistency
- **Coverage**: Measure and track progress
- **Reporting**: Clear findings with remediation
- **CI/CD**: Catch issues early
