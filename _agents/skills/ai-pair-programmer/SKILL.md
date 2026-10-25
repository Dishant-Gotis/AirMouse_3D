---
skill_name: ai-pair-programmer
description: Complete AI-assisted development workflow including planning, implementation, testing, review loops, and handoff patterns
category: AI & Claude Code Mastery
version: 1.0.0
---

# AI Pair Programmer: Full-Cycle Collaborative Development

This skill teaches how to work effectively with AI as a programming partner, from initial planning through testing, review, and handoff. Master the patterns that make AI-assisted development feel natural and productive.

## Part 1: The Pair Programming Model

### What is AI Pairing?

In traditional pair programming (two humans at one keyboard):
- **Driver** writes code
- **Navigator** reviews, suggests, catches issues
- Roles swap frequently

With AI pairing:
- **You (Driver)**: Make decisions, understand code, write tests, review
- **Claude Code (Navigator)**: Write code, suggest patterns, refactor, explain

This is asymmetrical—you always maintain decision authority.

### Pairing Protocols

**Passive**: "Just generate code for me"
Result: Disconnected, unmaintainable code

**Active**: "Let me understand each step, question assumptions, verify logic"
Result: Ownership, learning, maintainability

## Part 2: Planning Phase

### Start with Clear Requirements

Before asking Claude to code, clarify:

```markdown
## Feature: Invoice Templates

### What
User can create reusable invoice templates with:
- Custom fields (company name, logo, colors)
- Predefined item lines (descriptions, rates)
- Save/load templates

### Why
Faster invoicing, consistency, professionalism

### Success Criteria
- Create template in <30 seconds
- Apply to new invoice in one click
- Can edit/delete templates

### Constraints
- Templates private to user
- Max 50 templates per user
- Can't delete template if in use
```

### Ask Claude for a Plan, Not Code

```
I want to add invoice templates. Here's the requirement: [above]

Before we code, what's your approach?
1. Database changes (schema)
2. API endpoints needed
3. Frontend components
4. Edge cases to handle
```

Claude responds with a plan. **Review and adjust before coding.**

### Example Plan Conversation

**You**: "I want user authentication via GitHub OAuth"

**Claude**:
"Here's what I'd implement:
1. Add OAuth callback route in backend
2. Store GitHub user ID in database
3. Issue JWT tokens for subsequent requests
4. Protect endpoints with JWT middleware
5. Add GitHub login button to frontend

Questions:
- Should old email/password auth still work?
- Need profile data from GitHub (name, avatar)?
- Store refresh tokens or just access tokens?"

**You**: "Keep email/password. Yes to profile. Just access tokens."

Now you're aligned before writing a single line of code.

## Part 3: Implementation Workflow

### Pattern 1: Guided Generation

Instead of: "Build this entire feature"

Use: "Show me the approach step-by-step"

```
Step 1: Create the database schema for templates.
Show me the Prisma model.

[Claude generates schema]

Step 2: Now create the API endpoint to save a template.
Route should be POST /api/templates

[Claude generates endpoint]

Step 3: Add validation. Templates must have:
- name (required, max 100 chars)
- items (required, max 20 items)
- colors (optional)

[Claude adds validation]
```

Each step is small, reviewable, and iterative.

### Pattern 2: Assumption Checking

When Claude generates code, explicitly check assumptions:

```typescript
// Claude generated this
export async function saveTemplate(data: TemplateInput) {
  const template = await db.template.create({
    data: {
      ...data,
      userId: getCurrentUser().id  // ← ASSUMPTION: What if user not authenticated?
    }
  });
  return template;
}
```

**Question the assumption**:
```
⚠️ What if getCurrentUser() returns null?
Should we throw an error? Return null? Let me see how you handle this.
```

Claude adjusts:
```typescript
export async function saveTemplate(data: TemplateInput, userId: string) {
  if (!userId) {
    throw new Error('User not authenticated');
  }
  // ...
}
```

### Pattern 3: Test-First Pairing

Test → Implementation → Refinement

**Step 1: Write test**
```
Create a test for the saveTemplate function.
Test that:
1. Valid data creates a template
2. Duplicate names are allowed (same user can have multiple)
3. Unauthenticated requests fail
```

Claude generates tests.

**Step 2: Write implementation**
```
Now implement saveTemplate to pass these tests.
Use the schema and validation we defined earlier.
```

Claude implements.

**Step 3: Run tests**
```bash
npm test
```

All pass? Good. Failed tests? Debug together.

## Part 4: Code Review & Refinement

### Code Review Checklist

After Claude generates code, you review using this checklist:

```markdown
## Code Review

- [ ] Does it match the plan we agreed on?
- [ ] Are there any security issues? (auth, validation, XSS)
- [ ] Error handling: What happens if things fail?
- [ ] Performance: Will this scale? Any N+1 queries?
- [ ] Types: Is everything properly typed?
- [ ] Tests: Do we have adequate coverage?
- [ ] Consistency: Does it match our CLAUDE.md conventions?
- [ ] Clarity: Is this code understandable to future me?
```

### Common Review Issues & Fixes

**Issue: Missing error handling**
```typescript
// Claude generated
export async function getUser(id: string) {
  const user = await db.user.findUnique({ where: { id } });
  return user; // What if not found?
}
```

**Your feedback:**
```
What if the user doesn't exist? Return null? Throw error?
Should match our API error pattern from CLAUDE.md.
```

**Issue: Inefficient queries**
```typescript
// Claude generated (inefficient)
const templates = await db.template.findMany({ where: { userId } });
const items = await Promise.all(
  templates.map(t => db.item.findMany({ where: { templateId: t.id } }))
); // N+1 query problem!
```

**Your feedback:**
```
This has an N+1 query problem. Should load items in one query.
Show me using Prisma's include syntax.
```

**Issue: Missing type safety**
```typescript
// Claude generated
const response = await fetch(url).then(r => r.json());
// What's the type of response?
```

**Your feedback:**
```
Type response as TemplateResponse. Add proper error handling for parsing.
```

## Part 5: Testing Workflow

### Unit Tests

```markdown
### Pattern: Testing Pure Functions

Test utility functions with multiple cases:

```typescript
import { calculateInvoiceTotal } from '@/lib/calculate';

describe('calculateInvoiceTotal', () => {
  it('sums items correctly', () => {
    const items = [
      { description: 'Service', amount: 100 },
      { description: 'Product', amount: 50 }
    ];
    expect(calculateInvoiceTotal(items)).toBe(150);
  });

  it('applies tax correctly', () => {
    const items = [{ description: 'Service', amount: 100 }];
    expect(calculateInvoiceTotal(items, 0.1)).toBe(110); // +10% tax
  });

  it('handles zero items', () => {
    expect(calculateInvoiceTotal([])).toBe(0);
  });
});
```
```

Ask Claude: "Write tests for [function] covering happy path, edge cases, and errors"

### Integration Tests

```typescript
describe('Invoice API', () => {
  it('POST /api/invoices creates an invoice', async () => {
    const response = await request(app)
      .post('/api/invoices')
      .send({
        clientName: 'ACME Corp',
        amount: 1000,
        dueDate: '2024-02-01'
      })
      .expect(201);

    expect(response.body.id).toBeDefined();
    expect(response.body.status).toBe('DRAFT');
  });

  it('forbids creation without authentication', async () => {
    await request(app)
      .post('/api/invoices')
      .send({ /* ... */ })
      .expect(401); // Unauthorized
  });
});
```

Ask Claude: "Write integration tests for the [endpoint] API, covering success and error cases"

### E2E Tests (if applicable)

```typescript
describe('Invoice workflow', () => {
  it('user can create, edit, and send invoice', async () => {
    // 1. Log in
    await page.goto('https://app.com/login');
    await page.fill('input[name="email"]', 'user@example.com');
    await page.click('button:has-text("Sign in")');

    // 2. Create invoice
    await page.click('button:has-text("New Invoice")');
    await page.fill('input[name="amount"]', '1000');
    await page.click('button:has-text("Save")');

    // 3. Verify created
    expect(await page.isVisible('text=Invoice #1001')).toBeTruthy();
  });
});
```

## Part 6: Refactoring & Optimization

### When to Refactor

**Don't refactor**:
- Features not yet shipped
- Code you don't understand yet

**Do refactor**:
- Working features with tests
- Before adding new features on top
- When code becomes duplicated (>2 copies)

### Refactoring Workflow

**Step 1: Understand**
```
I want to refactor this function.
Here's the current code: [paste]

What do you see? Are there issues?
```

**Step 2: Plan**
```
I'd like to:
1. Extract validation to a separate function
2. Use a builder pattern for template creation
3. Add caching for frequently used templates

Does this make sense?
```

**Step 3: Implement**
```
Refactor the template creation flow using a builder pattern.
Keep tests passing throughout.
```

**Step 4: Verify**
```bash
npm test     # All tests pass?
npm run lint # Code style?
npm run type-check # TypeScript strict?
```

## Part 7: Handoff Patterns

### End-of-Session Handoff

When stopping work, create a handoff document:

```markdown
## Session Handoff: Invoice Templates Feature

### What Was Done
- [x] Database schema for templates
- [x] API endpoints (create, list, update, delete)
- [x] Frontend components (Create, List, Edit)
- [ ] Email sending when invoice created from template

### Current State
- All tests passing
- No console errors
- Feature works end-to-end

### Open Questions
- Should templates support custom CSS?
- Should we allow template sharing with team members?

### Next Steps
1. [ ] User testing (5 users)
2. [ ] Polish animations/UX
3. [ ] Implement email sending
4. [ ] Deploy to production

### Files Modified
- `/src/db/schema.prisma` (added Template model)
- `/src/api/templates.ts` (endpoints)
- `/src/components/TemplateForm.tsx` (new)
- `/src/components/TemplateList.tsx` (new)
- `/src/__tests__/templates.test.ts` (new)
```

Save this in your project repository or memory system.

### Code Handoff to Team

When handing off to a team member:

```
Here's what I built:
1. Database: New Template table (see schema.prisma)
2. API: CRUD endpoints at /api/templates
3. Frontend: Components in /src/components/

Code review: All tests pass, follows CLAUDE.md conventions

How to extend:
- Add more fields to TemplateInput schema
- Create new Template API endpoints using the existing pattern
- Update TemplateForm component for new fields

Questions? See CLAUDE.md or ask.
```

## Part 8: Common Pairing Pitfalls

### Pitfall 1: Over-Reliance

❌ "Just generate it all. I'll use it as-is."
✅ "Generate it. I'll review, understand, and improve it."

You must understand the code. If you don't, ask Claude to explain.

### Pitfall 2: Trusting Without Verification

❌ "Claude said it's secure, so it must be"
✅ "Claude generated it. Let me review the security implications."

Security, performance, and architecture need human judgment.

### Pitfall 3: Insufficient Testing

❌ "Unit tests are enough"
✅ "Unit tests + integration tests + manual testing"

AI-generated code deserves skeptical testing.

### Pitfall 4: Poor Communication

❌ Vague requests: "Fix this"
✅ Clear requests: "Refactor this function to use early returns and reduce nesting"

Good prompts get good code.

### Pitfall 5: Ignoring Context

❌ Asking Claude the same thing every session
✅ Maintaining CLAUDE.md so Claude remembers your patterns

Context is cheap; hallucination is expensive.

## Part 9: Communication Patterns

### Pattern 1: Think Out Loud

```
I'm looking at this component. It's doing too much:
1. Fetching data
2. Rendering form
3. Handling validation
4. Managing loading state

Should we split it into smaller components?
```

Claude responds with ideas.

### Pattern 2: Socratic Questioning

Instead of: "Fix this"

Ask: "What's the issue here? How would you fix it?"

Claude explains. You learn. You make decisions.

### Pattern 3: Disagreement

When Claude suggests something you disagree with:

```
You suggested using Redux. But we're using Zustand.
Can you re-implement this using Zustand instead?
```

Claude adjusts. No ego.

## Part 10: Pairing Maturity Levels

### Level 1: Passive
```
Me: Generate a login form
Claude: [Generates code]
Me: Paste into project
Result: Disconnected, don't understand it
```

### Level 2: Active
```
Me: Generate a login form
Claude: [Generates code]
Me: Review, ask questions, refine
Result: Working code I understand
```

### Level 3: Collaborative
```
Me: Show me a plan for authentication
Claude: [Explains approach]
Me: Questions and adjustments
Claude: Refined plan
Me: Implement step-by-step with feedback
Result: Clean, owned code
```

### Level 4: Mastery
```
Me: I want to refactor the data layer
Claude: Here's what I see. Three approaches:
A) Extract repository pattern
B) Use Query/Command pattern
C) Implement GraphQL

Which feels right?
Me: A, but with these modifications
Claude: [Implements A with modifications]
Me: Review, iterate, ship
Result: Architectural improvement
```

## Checklist: Pair Programmer Ready

- ✓ Write plan before asking for code
- ✓ Review every generated chunk
- ✓ Test thoroughly (unit + integration)
- ✓ Understand the code (ask if confused)
- ✓ Maintain decision authority
- ✓ Communicate clearly (detailed, not vague)
- ✓ Use proper handoff patterns
- ✓ Verify assumptions, don't assume
- ✓ Keep CLAUDE.md updated
- ✓ Aim for Level 3-4 maturity

Effective AI pairing feels like working with a thoughtful colleague who's always available and infinitely patient.
