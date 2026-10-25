---
skill_name: Accessibility Testing Guide
description: Test with Axe, Lighthouse, screen readers, and manual accessibility validation
category: Testing
version: 1.0.0
---

# Accessibility Testing Guide

## Overview
Accessibility testing ensures applications work for all users. Master Axe, Lighthouse, screen reader testing, and WCAG compliance.

## Axe Accessibility Engine

### Jest Integration

```javascript
import { axe, toHaveNoViolations } from 'jest-axe';
import { render } from '@testing-library/react';

expect.extend(toHaveNoViolations);

describe('Login Form Accessibility', () => {
  it('should not have any accessibility violations', async () => {
    const { container } = render(<LoginForm />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
```

### Cypress Integration

```javascript
describe('Accessibility Audit', () => {
  beforeEach(() => {
    cy.visit('/');
    cy.injectAxe();
  });

  it('homepage has no violations', () => {
    cy.checkA11y();
  });

  it('form has no violations', () => {
    cy.get('form').then(form => {
      cy.checkA11y(form);
    });
  });

  it('reports specific violations', () => {
    cy.checkA11y(null, {
      rules: {
        'color-contrast': { enabled: true },
        'button-name': { enabled: true }
      }
    });
  });
});
```

### Axe DevTools Report

```javascript
const { AxeBuilder } = require('@axe-core/playwright');

async function auditPage(url) {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto(url);

  const results = await new AxeBuilder({ page })
    .analyze();

  return {
    violations: results.violations,
    passes: results.passes,
    inapplicable: results.inapplicable,
    impact: results.violations.reduce((sum, v) => {
      const impacts = { critical: 3, serious: 2, moderate: 1, minor: 0 };
      return sum + (impacts[v.impact] || 0);
    }, 0)
  };
}
```

## Lighthouse Accessibility Audit

### Automated Lighthouse Testing

```javascript
import lighthouse from 'lighthouse';
import chromeLauncher from 'chrome-launcher';

async function runLighthouseAudit(url) {
  const chrome = await chromeLauncher.launch({ chromeFlags: ['--headless'] });

  const options = {
    logLevel: 'info',
    output: 'json',
    port: chrome.port,
    onlyCategories: ['accessibility']
  };

  const runnerResult = await lighthouse(url, options);
  await chromeLauncher.kill(chrome.pid);

  const report = runnerResult.lhr;
  return {
    score: report.categories.accessibility.score * 100,
    audits: report.audits,
    issues: Object.values(report.audits)
      .filter(audit => audit.score < 1)
      .map(audit => ({
        title: audit.title,
        description: audit.description,
        items: audit.details?.items || []
      }))
  };
}

// Usage
const results = await runLighthouseAudit('https://example.com');
console.log(`Accessibility Score: ${results.score}`);
```

### CI/CD Integration

```yaml
# .github/workflows/lighthouse.yml
name: Lighthouse
on: [push, pull_request]

jobs:
  lighthouse:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3

      - name: Run Lighthouse
        run: npm run audit:lighthouse

      - name: Upload report
        uses: actions/upload-artifact@v3
        with:
          name: lighthouse-report
          path: lighthouse-report.html

      - name: Check accessibility score
        run: |
          SCORE=$(cat lighthouse-results.json | jq '.categories.accessibility.score * 100')
          if (( $(echo "$SCORE < 90" | bc -l) )); then
            echo "Accessibility score too low: $SCORE"
            exit 1
          fi
```

## Screen Reader Testing

### NVDA Setup (Windows)

```bash
# Download NVDA (free screen reader)
# https://www.nvaccess.org/download/

# Test with NVDA
# 1. Enable NVDA
# 2. Navigate using Tab, arrow keys
# 3. Listen to announcements
# 4. Test forms, buttons, links
```

### VoiceOver Testing (macOS)

```bash
# Enable VoiceOver: Cmd + F5

# Test navigation:
# - VO + Arrow keys to navigate
# - VO + U for rotor (headings, links)
# - VO + Space to interact
# - Tab to move between focusable elements
```

### Programmatic Screen Reader Testing

```javascript
describe('Screen Reader Announcements', () => {
  it('announces button purpose', async () => {
    const { container } = render(
      <button aria-label="Close notification">X</button>
    );

    // Screen reader should announce "Close notification button"
    const button = container.querySelector('button');
    expect(button).toHaveAccessibleName('Close notification');
  });

  it('announces form errors', async () => {
    const { getByRole } = render(
      <form>
        <input aria-label="Email" aria-invalid="true" aria-describedby="error" />
        <span id="error">Email is invalid</span>
      </form>
    );

    const input = getByRole('textbox', { name: 'Email' });
    expect(input).toHaveAttribute('aria-invalid', 'true');
    expect(input).toHaveAttribute('aria-describedby', 'error');
  });

  it('announces live region updates', async () => {
    const { getByRole } = render(
      <div aria-live="polite" aria-label="Status">
        Loading...
      </div>
    );

    // Screen reader announces: "Status: Loading..."
    const region = getByRole('status');
    expect(region).toBeInTheDocument();
  });
});
```

## WCAG Compliance Testing

### WCAG 2.1 Level AA Checklist

```javascript
class WCAGTester {
  tests = [
    {
      criterion: '1.4.3 Contrast (Minimum)',
      test: async (page) => {
        // Check all text has contrast ratio >= 4.5:1
        const elements = await page.locator('text=*').all();
        for (const el of elements) {
          const color = await el.evaluate(el => {
            const style = window.getComputedStyle(el);
            return {
              color: style.color,
              background: style.backgroundColor
            };
          });
          // Validate contrast ratio
        }
      }
    },
    {
      criterion: '2.1.1 Keyboard',
      test: async (page) => {
        // All functionality available via keyboard
        // Tab through all interactive elements
        await page.keyboard.press('Tab');
        expect(page.locator(':focus')).toBeTruthy();
      }
    },
    {
      criterion: '2.4.3 Focus Order',
      test: async (page) => {
        // Tab order is logical
        const focusOrder = [];
        for (let i = 0; i < 20; i++) {
          focusOrder.push(await page.evaluate(() => {
            return document.activeElement.id;
          }));
          await page.keyboard.press('Tab');
        }
        // Verify order is logical
      }
    },
    {
      criterion: '4.1.2 Name, Role, Value',
      test: async (page) => {
        // All interactive elements have accessible names
        const buttons = await page.locator('button').all();
        for (const btn of buttons) {
          const name = await btn.getAttribute('aria-label')
            || await btn.textContent();
          expect(name).toBeTruthy();
        }
      }
    }
  ];

  async runAll(page) {
    const results = [];
    for (const test of this.tests) {
      try {
        await test.test(page);
        results.push({ criterion: test.criterion, passed: true });
      } catch (error) {
        results.push({
          criterion: test.criterion,
          passed: false,
          error: error.message
        });
      }
    }
    return results;
  }
}
```

## Common Accessibility Issues

### Semantic HTML

```javascript
// BAD: Div used as button
<div onclick="handleClick()">Submit</div>

// GOOD: Semantic button
<button onClick={handleClick}>Submit</button>

// BAD: No heading structure
<span style="font-size: 24px; font-weight: bold">Title</span>

// GOOD: Semantic heading
<h1>Title</h1>

// BAD: Image without alt text
<img src="logo.png" />

// GOOD: Descriptive alt text
<img src="logo.png" alt="Company logo" />
```

### ARIA Attributes

```javascript
// Announce dynamic content
<div aria-live="polite" aria-label="Notifications">
  {notifications.map(n => <p key={n.id}>{n.message}</p>)}
</div>

// Label complex controls
<input aria-label="Search products" type="search" />

// Describe form errors
<input aria-invalid="true" aria-describedby="error-msg" />
<span id="error-msg">Email format is invalid</span>

// Hide decorative elements
<span aria-hidden="true">→</span>
```

## Manual Testing Procedures

### Keyboard Navigation Testing

```markdown
# Keyboard Navigation Checklist

- [ ] Tab through all pages
- [ ] Tab order follows visual flow
- [ ] No keyboard traps (can't escape elements)
- [ ] Focus indicator visible everywhere
- [ ] Enter/Space activate buttons
- [ ] Arrow keys work in dropdowns
- [ ] Escape closes modals
- [ ] Skip links work correctly
```

### Color Contrast Testing

```javascript
// Use contrast checker
// WebAIM: https://webaim.org/resources/contrastchecker/
// Specs:
// - Normal text: 4.5:1 ratio (Level AA)
// - Large text: 3:1 ratio (Level AA)
// - Graphics: 3:1 ratio

const contrastRatio = (color1, color2) => {
  const lum1 = getRelativeLuminance(color1);
  const lum2 = getRelativeLuminance(color2);
  const lighter = Math.max(lum1, lum2);
  const darker = Math.min(lum1, lum2);
  return (lighter + 0.05) / (darker + 0.05);
};
```

## Production Checklist

- [ ] Run Axe on all pages (automated)
- [ ] Achieve Lighthouse accessibility score >90
- [ ] Test with screen reader (NVDA, JAWS, VoiceOver)
- [ ] Test keyboard-only navigation
- [ ] Verify focus indicators visible
- [ ] Check color contrast ratios
- [ ] Validate semantic HTML structure
- [ ] Test form error announcements
- [ ] Verify ARIA labels where needed
- [ ] Test with zoom at 200%
- [ ] Conduct manual accessibility review
- [ ] Document accessibility testing procedures
- [ ] Include accessibility in CI/CD pipeline
- [ ] Train team on accessibility best practices
