---
skill_name: accessibility-implementation
description: A11y - ARIA roles, focus management, keyboard navigation, screen reader testing
category: Frontend Development
version: 1.0.0
---

# Accessibility (A11y) Implementation

## ARIA Roles and Attributes

Semantic HTML first, ARIA as supplement:

```html
<!-- Good: Semantic HTML -->
<button>Submit</button>
<nav>Navigation</nav>

<!-- Bad: Generic div with ARIA -->
<div role="button">Submit</div>

<!-- When semantic isn't available, use ARIA -->
<div role="tablist">
  <div role="tab" aria-selected="true">Tab 1</div>
  <div role="tab" aria-selected="false">Tab 2</div>
</div>
```

Common ARIA attributes:

```html
<!-- aria-label: Label when no text -->
<button aria-label="Close menu">✕</button>

<!-- aria-labelledby: Link to label element -->
<h2 id="dialog-title">Confirm Action</h2>
<div role="dialog" aria-labelledby="dialog-title">...</div>

<!-- aria-describedby: Additional description -->
<input aria-describedby="pwd-hint" type="password" />
<p id="pwd-hint">8+ chars, include numbers</p>

<!-- aria-expanded: Collapsible state -->
<button aria-expanded="false" aria-controls="menu">Menu</button>
<ul id="menu" hidden>...</ul>

<!-- aria-live: Announce dynamic updates -->
<div aria-live="polite" aria-atomic="true">
  Items added: 5
</div>
```

## Focus Management

```typescript
'use client'

import { useRef, useEffect } from 'react'

export function Modal({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
  const dialogRef = useRef<HTMLDivElement>(null)
  const firstButtonRef = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    if (isOpen && firstButtonRef.current) {
      // Focus first button when modal opens
      firstButtonRef.current.focus()
    }
  }, [isOpen])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      onClose()
    }
  }

  return (
    <div
      ref={dialogRef}
      role="dialog"
      aria-labelledby="modal-title"
      onKeyDown={handleKeyDown}
    >
      <h2 id="modal-title">Confirm</h2>
      <button ref={firstButtonRef} onClick={onClose}>
        Cancel
      </button>
      <button onClick={() => { /* save */ }}>Save</button>
    </div>
  )
}
```

## Keyboard Navigation

```typescript
export function Menu() {
  const [activeIndex, setActiveIndex] = useState(0)
  const items = ['Home', 'About', 'Contact']

  const handleKeyDown = (e: React.KeyboardEvent) => {
    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault()
        setActiveIndex((prev) => (prev + 1) % items.length)
        break
      case 'ArrowUp':
        e.preventDefault()
        setActiveIndex((prev) => (prev - 1 + items.length) % items.length)
        break
      case 'Enter':
        // Activate item
        break
    }
  }

  return (
    <div role="menubar" onKeyDown={handleKeyDown}>
      {items.map((item, i) => (
        <button
          key={i}
          role="menuitem"
          aria-selected={activeIndex === i}
          tabIndex={activeIndex === i ? 0 : -1}
        >
          {item}
        </button>
      ))}
    </div>
  )
}
```

## Form Accessibility

```html
<!-- Good: Label properly associated -->
<label htmlFor="email">Email</label>
<input id="email" type="email" required />

<!-- Error messaging -->
<label htmlFor="password">Password</label>
<input
  id="password"
  type="password"
  aria-describedby="pwd-error"
  aria-invalid="true"
/>
<span id="pwd-error" role="alert">Password too short</span>

<!-- Radio groups -->
<fieldset>
  <legend>Choose color</legend>
  <label>
    <input type="radio" name="color" value="red" />
    Red
  </label>
  <label>
    <input type="radio" name="color" value="blue" />
    Blue
  </label>
</fieldset>
```

## Skip Navigation

Allow users to skip to main content:

```html
<a href="#main-content" className="sr-only">
  Skip to main content
</a>

<nav>Navigation...</nav>

<main id="main-content">Content</main>

<!-- CSS: Hide visually but keep for screen readers -->
<style>
  .sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
  }
</style>
```

## Color Contrast

```css
/* WCAG AA: 4.5:1 ratio for normal text, 3:1 for large text -->
body {
  color: #1a1a1a; /* Dark text */
  background: #ffffff; /* Light background */
  /* Contrast ratio: 21:1 */
}

/* Tool: WebAIM Contrast Checker */
```

## Testing for Accessibility

```typescript
import { render, screen } from '@testing-library/react'
import { axe, toHaveNoViolations } from 'jest-axe'

expect.extend(toHaveNoViolations)

describe('Button accessibility', () => {
  it('has accessible name', () => {
    render(<button>Click me</button>)
    expect(screen.getByRole('button', { name: /click/i })).toBeInTheDocument()
  })

  it('has no WCAG violations', async () => {
    const { container } = render(<button>Click</button>)
    const results = await axe(container)
    expect(results).toHaveNoViolations()
  })
})
```

## Key Accessibility Principles

1. **Perceivable**: Text alternatives, distinguishable colors
2. **Operable**: Keyboard navigation, skip links, focus visible
3. **Understandable**: Clear labels, consistent navigation
4. **Robust**: Valid HTML, ARIA correct usage

## Tools

- **axe DevTools**: Browser extension for audits
- **WAVE**: Web accessibility evaluation
- **Lighthouse**: Built into Chrome DevTools
- **Screen Readers**: NVDA (Windows), JAWS, VoiceOver (Mac)

## Key Takeaways

- Use semantic HTML first
- ARIA supplements, not replaces
- Test with keyboard navigation
- Manage focus in modals/dropdowns
- Color contrast ratio 4.5:1
- Test with automated and manual tools
