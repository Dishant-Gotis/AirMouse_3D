---
skill_name: Accessibility Compliance Guide
description: Implement WCAG 2.2 accessibility standards, audit, remediate, and test for inclusive web
category: Miscellaneous High-Value
version: 1.0.0
---

# Accessibility Compliance Guide

## WCAG 2.2 Standards

### Principles & Levels
```
WCAG (Web Content Accessibility Guidelines):
1. Perceivable (can users perceive content?)
2. Operable (can users navigate?)
3. Understandable (can users understand?)
4. Robust (works with assistive tech?)

Conformance levels:
- A: Minimum compliance
- AA: Better compliance (recommended)
- AAA: Highest compliance (extensive)

Recommendation: Target AA for most sites
AAA for educational/government sites
```

### Key Standards
```
WCAG 2.2 common requirements:

1. Perceivable
   - Alternative text for images
   - Captions for audio/video
   - Sufficient contrast (4.5:1 for text)
   - Resizable text
   - No seizure-inducing content

2. Operable
   - Keyboard accessible (Tab key)
   - Focus indicators (visible)
   - Skip navigation links
   - No auto-play/auto-advance
   - No keyboard traps

3. Understandable
   - Clear language (reading level appropriate)
   - Consistent navigation
   - Error messages (clear, helpful)
   - Clear instructions
   - Readable fonts/sizing

4. Robust
   - Valid HTML
   - ARIA labels (semantic)
   - Works with screen readers
   - Compatible with browsers
```

## Accessibility Audit

### Automated Testing
```
Tools:
- axe (Deque): Most accurate
- WAVE (WebAIM): Visual feedback
- Lighthouse (Google): Part of DevTools
- Accessibility Insights (Microsoft)
- NVDA (screen reader, free)

Running Lighthouse audit:
1. Chrome DevTools > Lighthouse
2. Select "Accessibility"
3. Run audit
4. Review issues (0-100 score)
5. Target: 90+ score
```

### Manual Testing
```
Keyboard navigation:
1. Disable mouse
2. Tab through site
3. Check all interactive elements accessible
4. Focus indicators visible
5. No keyboard traps

Screen reader testing:
1. Download NVDA (free, Windows) or VoiceOver (macOS)
2. Enable screen reader
3. Navigate site
4. Check all content announced
5. Check image alt text
6. Check form labels

Color contrast:
1. Use WebAIM contrast checker
2. Check heading contrast
3. Check button contrast
4. Check link contrast
5. Target: 4.5:1 (AA), 7:1 (AAA)
```

## Common Accessibility Issues & Fixes

### Images & Alt Text
```html
<!-- BAD: No alt text -->
<img src="team.jpg">

<!-- GOOD: Descriptive alt text -->
<img src="team.jpg" alt="Team photo at 2024 company retreat">

<!-- BAD: Redundant alt text -->
<img src="icon.png" alt="Icon">

<!-- GOOD: Meaningful alt text -->
<img src="checkmark.png" alt="Completed task">

<!-- Decorative images: empty alt -->
<img src="divider.png" alt="">

<!-- Complex images: use longdesc -->
<img src="chart.png" alt="Sales chart"
     longdesc="Sales increased 25% in Q1">
```

### Forms & Labels
```html
<!-- BAD: No label, unclear -->
<input type="text">

<!-- GOOD: Associated label -->
<label for="email">Email address:</label>
<input type="email" id="email" name="email" required>

<!-- Error messages: linked to input -->
<label for="password">Password:</label>
<input type="password" id="password" aria-describedby="pwd-error">
<span id="pwd-error">Password must be 8+ characters</span>

<!-- Form instructions: before form -->
<p>All fields marked with * are required</p>
<form>
  <label>Name* <input required></label>
</form>
```

### Color Contrast
```css
/* BAD: Low contrast (1.2:1) */
body {
  color: #777;
  background: #999;
}

/* GOOD: High contrast (7:1) */
body {
  color: #000;
  background: #fff;
}

/* WCAG AA: 4.5:1 minimum
   WCAG AAA: 7:1 minimum
   Tool: https://webaim.org/resources/contrastchecker/
*/
```

### Keyboard Navigation
```html
<!-- Skip to main content (accessibility best practice) -->
<a href="#main-content" class="skip-link">Skip to main content</a>

<nav>Navigation menu</nav>

<main id="main-content">
  Main content here
</main>

<!-- CSS for skip link (hidden until focused) -->
<style>
.skip-link {
  position: absolute;
  top: -40px;
}

.skip-link:focus {
  top: 0;
  z-index: 100;
}
</style>
```

### ARIA Attributes
```html
<!-- Landmark roles (help screen reader) -->
<nav role="navigation" aria-label="Main navigation">
  <ul>
    <li><a href="/">Home</a></li>
  </ul>
</nav>

<!-- Live regions (announce dynamic content) -->
<div aria-live="polite" aria-atomic="true">
  Updated: Product count is 5
</div>

<!-- Form errors (link to input) -->
<input id="email" type="email" aria-describedby="email-error">
<span id="email-error">Invalid email format</span>

<!-- Buttons with icon (needs label) -->
<button aria-label="Close dialog">✕</button>

<!-- Toggle button state -->
<button aria-pressed="false" onclick="toggleDarkMode()">
  Dark mode
</button>
```

## Testing with Assistive Technology

### NVDA (Windows)
```bash
# Download: https://www.nvaccess.org/

# Start NVDA
# Ctrl + Alt + N

# Navigation:
NVDA + Down Arrow = Read current line
NVDA + Right Arrow = Next word
Tab = Next interactive element
Shift + Tab = Previous interactive element
H = Next heading
L = Next link

# Heading structure must be logical (H1, H2, H3)
# Skipping heading levels breaks navigation
```

### VoiceOver (macOS)
```bash
# Enable: System Preferences > Accessibility > VoiceOver

# Start: Cmd + F5

# Navigation:
VO + Right Arrow = Next item
VO + Left Arrow = Previous item
VO + U = Rotor (navigate by headings, links, etc)
Tab = Interactive elements
```

## Remediation Priority

### High Priority (Fix First)
```
1. Missing alt text on images
2. Missing form labels
3. Low contrast text (< 4.5:1)
4. Missing heading structure (H1, H2, H3)
5. Keyboard traps
6. Auto-play videos/sounds
```

### Medium Priority
```
7. Links unclear (e.g., "click here")
8. Missing skip navigation
9. ARIA errors
10. Focus indicators unclear
```

### Low Priority
```
11. Language tag missing
12. Font sizing issues (minor)
13. Complex language (professional jargon)
```

## Accessibility Testing Checklist

```
Visual:
[ ] Color contrast 4.5:1 (AA) or higher
[ ] No reliance on color alone (patterns/icons)
[ ] Text resizable to 200%
[ ] Focus indicator visible

Navigation:
[ ] Tab order logical
[ ] All interactive elements keyboard accessible
[ ] No keyboard traps
[ ] Skip navigation link present

Content:
[ ] Descriptive alt text on images
[ ] Proper heading structure (H1, H2, H3)
[ ] Form labels associated
[ ] Error messages clear

Audio/Video:
[ ] Captions on all video
[ ] Transcripts on audio
[ ] No auto-play

Tools:
[ ] Lighthouse audit 90+
[ ] WAVE report no errors
[ ] NVDA/VoiceOver tested
[ ] Keyboard-only tested
[ ] Color contrast checked
```

## Accessibility Statement

```
Create accessibility statement (footer link):

"We are committed to accessibility. If you encounter any barriers,
please contact: accessibility@company.com

Known limitations:
- PDFs may not be fully accessible
- Videos require captions (in progress)

Accessibility features:
- Keyboard navigation
- High contrast mode
- Text resizing
- Skip navigation
- Accessible forms"
```

## Best Practices
1. Test with real screen readers
2. Keyboard navigation first
3. Semantic HTML (proper heading/nav tags)
4. Color contrast 4.5:1 minimum
5. ARIA labels for unclear elements
6. Accessible forms (labels + errors)
7. Alt text on all images
8. Captions on all video
9. Regular accessibility audits
10. Include people with disabilities in testing
