---
skill_name: accessibility-testing
description: Accessibility testing - axe-core, jest-axe, screen reader testing, and keyboard navigation
category: Testing & Quality
version: 1.0.0
---

# Accessibility Testing

## axe-core Integration

Install axe-core:

```bash
npm install -D axe-core jest-axe
```

Basic accessibility test:

```javascript
import { axe, toHaveNoViolations } from 'jest-axe';
import { render } from '@testing-library/react';
import Button from './Button';

expect.extend(toHaveNoViolations);

describe('Button Accessibility', () => {
  it('should not have any accessibility violations', async () => {
    const { container } = render(<Button>Click me</Button>);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('should have proper ARIA labels', async () => {
    const { container } = render(
      <Button aria-label="Close dialog">×</Button>
    );
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
```

## Playwright Accessibility Testing

```typescript
import { test, expect } from '@playwright/test';
import { injectAxe, checkA11y } from 'axe-playwright';

test('homepage should be accessible', async ({ page }) => {
  await page.goto('/');
  await injectAxe(page);
  await checkA11y(page);
});

test('should check specific regions', async ({ page }) => {
  await page.goto('/');
  await injectAxe(page);

  // Check only navigation
  await checkA11y(page, 'nav');

  // Check with exclusions
  await checkA11y(page, null, {
    rules: {
      'color-contrast': { enabled: false }
    }
  });
});
```

## Cypress Accessibility Testing

```typescript
import { injectAxe, checkA11y } from 'axe-cypress';

describe('Form Accessibility', () => {
  beforeEach(() => {
    cy.visit('/form');
    injectAxe();
  });

  it('form should be accessible', () => {
    checkA11y();
  });

  it('form fields should have labels', () => {
    cy.get('input').each(($input) => {
      const id = $input.attr('id');
      cy.get(`label[for="${id}"]`).should('exist');
    });

    injectAxe();
    checkA11y();
  });

  it('should have proper heading hierarchy', () => {
    cy.get('h1').should('have.length', 1);  // One H1
    cy.get('h2').should('have.length.greaterThan', 0);

    injectAxe();
    checkA11y();
  });
});
```

## Screen Reader Testing

Test with ARIA attributes:

```typescript
describe('Screen Reader Support', () => {
  it('should announce loading state', async () => {
    const { container } = render(<LoadingButton />);

    const loader = container.querySelector('[role="status"]');
    expect(loader).toHaveAttribute('aria-live', 'polite');
    expect(loader).toHaveTextContent('Loading...');
  });

  it('should announce errors', async () => {
    const { getByRole } = render(<Form onSubmit={mockError} />);

    const alert = getByRole('alert');
    expect(alert).toHaveAttribute('aria-live', 'assertive');
    expect(alert).toHaveTextContent('Error submitting form');
  });

  it('should manage focus properly', async () => {
    const { getByRole } = render(<Modal isOpen={true} />);

    const modal = getByRole('dialog');
    expect(modal).toHaveFocus();
  });
});
```

## Keyboard Navigation Testing

```typescript
describe('Keyboard Navigation', () => {
  it('should navigate menu with arrow keys', async () => {
    const { getByRole } = render(<Menu />);
    const menu = getByRole('menu');

    menu.focus();

    // Arrow down
    fireEvent.keyDown(menu, { key: 'ArrowDown' });
    expect(getByRole('menuitem', { name: /first/i })).toHaveFocus();

    // Arrow down again
    fireEvent.keyDown(menu, { key: 'ArrowDown' });
    expect(getByRole('menuitem', { name: /second/i })).toHaveFocus();

    // Arrow up
    fireEvent.keyDown(menu, { key: 'ArrowUp' });
    expect(getByRole('menuitem', { name: /first/i })).toHaveFocus();

    // Escape
    fireEvent.keyDown(menu, { key: 'Escape' });
    expect(menu).not.toHaveFocus();
  });

  it('should support tab navigation', async () => {
    const { getByRole } = render(<Form />);

    const firstInput = getByRole('textbox', { name: /first/i });
    const secondInput = getByRole('textbox', { name: /second/i });
    const submitButton = getByRole('button', { name: /submit/i });

    firstInput.focus();
    expect(firstInput).toHaveFocus();

    fireEvent.keyDown(firstInput, { key: 'Tab' });
    // (Tab handling depends on browser/testing setup)

    submitButton.focus();
    expect(submitButton).toHaveFocus();
  });
});
```

## Color Contrast Testing

```typescript
import { render } from '@testing-library/react';
import { axe } from 'jest-axe';

describe('Color Contrast', () => {
  it('should have sufficient color contrast', async () => {
    const { container } = render(
      <div style={{ color: '#333', backgroundColor: '#fff' }}>
        Text with good contrast
      </div>
    );

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('should fail with insufficient contrast', async () => {
    const { container } = render(
      <div style={{ color: '#ccc', backgroundColor: '#fff' }}>
        Text with poor contrast
      </div>
    );

    const results = await axe(container);
    expect(results.violations).toHaveLength.greaterThan(0);
  });
});
```

## ARIA Testing

```typescript
describe('ARIA Attributes', () => {
  it('button should have aria-pressed when toggle', () => {
    const { getByRole } = render(<ToggleButton />);
    const button = getByRole('button');

    expect(button).toHaveAttribute('aria-pressed', 'false');

    fireEvent.click(button);
    expect(button).toHaveAttribute('aria-pressed', 'true');
  });

  it('dialog should have proper attributes', () => {
    const { getByRole } = render(<Dialog title="Confirm" />);
    const dialog = getByRole('dialog');

    expect(dialog).toHaveAttribute('aria-labelledby');
    expect(dialog).toHaveAttribute('aria-modal', 'true');
  });

  it('combobox should manage aria-expanded', () => {
    const { getByRole } = render(<Select />);
    const combobox = getByRole('combobox');

    expect(combobox).toHaveAttribute('aria-expanded', 'false');

    fireEvent.click(combobox);
    expect(combobox).toHaveAttribute('aria-expanded', 'true');
  });
});
```

## Automated Accessibility Audits in CI

GitHub Actions:

```yaml
name: Accessibility Tests

on: [push, pull_request]

jobs:
  a11y:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
      - run: npm ci
      - run: npm run build
      - run: npm run start &
      - run: sleep 5
      - run: npm run test:a11y
      - uses: actions/upload-artifact@v3
        if: failure()
        with:
          name: a11y-report
          path: accessibility-report/
```

## Best Practices

1. **Test with screen readers** - NVDA, JAWS, VoiceOver
2. **Keyboard navigation** - All interactive elements
3. **Color contrast ratios** - WCAG AA minimum
4. **ARIA attributes** - Proper roles and states
5. **Heading hierarchy** - One H1, logical nesting
6. **Alt text for images** - Descriptive and concise
7. **Form labels** - Associated with inputs
8. **Automated testing** - axe-core in every test suite
