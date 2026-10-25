---
skill_name: autonomous-task-runner
description: Build self-correcting autonomous agents that plan, execute, test, and fix their own work with built-in guardrails
category: AI & Claude Code Mastery
version: 1.0.0
---

# Autonomous Task Runner: Self-Healing Agents

This skill teaches how to design autonomous agents that operate independently while maintaining safety guardrails, error recovery, and quality assurance. Learn to build the scaffolding for AI to run tasks with minimal human oversight.

## Part 1: Agent Architecture

### Agent Loop Pattern

An autonomous agent follows this loop:

```
1. Plan: "What am I supposed to do?"
2. Execute: "Do the task"
3. Verify: "Did it work?"
4. Fix: "If not, what went wrong?"
5. Report: "Here's what happened"
```

### Simple Agent Example

Goal: "Refactor all functions in /src/api to use early returns"

```javascript
const RefactorAgent = {
  async run() {
    // Step 1: Plan
    const plan = await this.createPlan();
    console.log('Plan:', plan);

    // Step 2: Execute
    const results = await this.executeTask(plan);
    console.log('Execution complete');

    // Step 3: Verify
    const errors = await this.verify(results);
    if (errors.length > 0) {
      // Step 4: Fix
      await this.fixErrors(errors);
      // Step 3 again: Re-verify
      const retryErrors = await this.verify(results);
      if (retryErrors.length > 0) {
        console.log('Gave up after retry:', retryErrors);
      }
    }

    // Step 5: Report
    return this.generateReport();
  },

  async createPlan() {
    return `
      1. Find all .ts files in /src/api
      2. For each file:
        a. Identify functions with multiple returns
        b. Refactor to use early returns
        c. Verify no logic changed
      3. Run tests to ensure nothing broke
    `;
  },

  async executeTask(plan) {
    // Ask Claude to execute the plan
    // Return list of modified files
  },

  async verify(results) {
    // Run linting, tests, type checking
    // Return list of errors
  },

  async fixErrors(errors) {
    // Ask Claude to fix the specific errors
  },

  generateReport() {
    // Summary of what was done
  }
};
```

## Part 2: Building Blocks

### Component 1: Goal Definition

Clear, measurable goals:

```javascript
const goals = [
  {
    id: 'fix-ts-errors',
    description: 'Resolve all TypeScript compilation errors',
    successCriteria: 'npm run type-check returns 0 errors',
    maxAttempts: 3,
    timeout: 5 * 60 * 1000 // 5 minutes
  },
  {
    id: 'add-tests',
    description: 'Write tests for auth module',
    successCriteria: 'Jest coverage >80% for /src/auth',
    maxAttempts: 5,
    timeout: 10 * 60 * 1000
  }
];
```

### Component 2: Task Breakdown

Complex goals need breaking into steps:

```javascript
async function breakDownTask(goal) {
  const steps = [
    { step: 1, action: 'Analyze current state', depends: [] },
    { step: 2, action: 'Create implementation plan', depends: [1] },
    { step: 3, action: 'Generate code changes', depends: [2] },
    { step: 4, action: 'Run automated tests', depends: [3] },
    { step: 5, action: 'Manual verification', depends: [4] }
  ];
  return steps;
}
```

### Component 3: Execution

```javascript
async function executeStep(step, context) {
  console.log(`Executing: ${step.action}`);

  try {
    const result = await performAction(step.action);
    return { success: true, result };
  } catch (error) {
    return { success: false, error: error.message };
  }
}
```

### Component 4: Verification

```javascript
async function verifyStep(step, result) {
  // Automated checks
  const checks = [
    { name: 'TypeScript compilation', check: () => runTypeCheck() },
    { name: 'Tests pass', check: () => runTests() },
    { name: 'Linting', check: () => runLint() },
    { name: 'No console errors', check: () => validateLogs() }
  ];

  const failures = [];
  for (const check of checks) {
    try {
      await check.check();
    } catch (error) {
      failures.push({ check: check.name, error: error.message });
    }
  }

  return {
    passed: failures.length === 0,
    failures
  };
}
```

### Component 5: Error Recovery

```javascript
async function handleFailure(failure, attempt) {
  if (attempt >= maxAttempts) {
    console.log(`Failed after ${attempt} attempts. Giving up.`);
    return { recovered: false, reason: 'Max attempts exceeded' };
  }

  console.log(`Attempt ${attempt} failed: ${failure.error}`);
  console.log(`Retrying...`);

  // Ask Claude to fix the specific error
  const fix = await askClaude(`
    The previous attempt failed with this error:
    ${failure.error}

    Here's the code that was generated:
    ${failure.generatedCode}

    How would you fix this?
  `);

  // Re-execute with the fix
  return await executeStep(currentStep, { ...context, fix });
}
```

## Part 3: Real Agent Examples

### Example 1: Dependency Upgrade Agent

Goal: "Upgrade React from 17 to 18"

```javascript
const ReactUpgradeAgent = {
  async run() {
    const plan = [
      'Read package.json and identify React version',
      'Check package-lock.json for conflicts',
      'Update package.json to React 18',
      'Run npm install',
      'Check for breaking changes',
      'Update code to use React 18 patterns',
      'Run tests to ensure nothing broke'
    ];

    for (const step of plan) {
      const result = await this.executeStep(step);
      if (!result.success) {
        const fixed = await this.fixError(result.error);
        if (!fixed) throw new Error(`Could not fix: ${step}`);
      }
    }

    return this.report();
  },

  async executeStep(step) {
    if (step.includes('Read package.json')) {
      return { success: true, data: require('./package.json') };
    }
    if (step.includes('Update package.json')) {
      return { success: true, data: 'React upgraded to v18' };
    }
    // ... other steps
  },

  async fixError(error) {
    // Ask Claude how to fix
    return await askClaude(`Error: ${error}. How to fix?`);
  },

  report() {
    return `✓ React upgraded from 17 to 18\n✓ All tests passing\n✓ No breaking changes`;
  }
};
```

### Example 2: Bug Fixing Agent

Goal: "Fix failing tests in the auth module"

```javascript
const BugFixAgent = {
  async run() {
    // 1. Identify failing tests
    const failingTests = await this.getFailingTests('auth');
    console.log(`Found ${failingTests.length} failing tests`);

    // 2. For each failing test
    for (const test of failingTests) {
      const fixed = await this.fixTest(test);
      if (!fixed) {
        console.log(`Could not fix: ${test.name}`);
        continue;
      }

      // 3. Verify fix
      const passing = await this.verifyTest(test);
      if (!passing) {
        console.log(`Fix didn't work for: ${test.name}`);
        await this.revert(test);
      }
    }

    return this.report();
  },

  async getFailingTests(module) {
    const output = await exec('npm test -- --testPathPattern=auth');
    return parseFailures(output);
  },

  async fixTest(test) {
    // Ask Claude to examine the test and suggest a fix
    const code = await readFile(test.file);
    const error = test.error;

    const suggestion = await askClaude(`
      Test: ${test.name}
      Error: ${error}
      Code:
      ${code}

      How would you fix this?
    `);

    if (!suggestion) return false;

    // Apply fix
    await writeFile(test.file, suggestion);
    return true;
  },

  async verifyTest(test) {
    const output = await exec(`npm test -- ${test.file}`);
    return output.includes('PASS');
  },

  report() {
    return `Fixed ${fixedCount} of ${totalCount} failing tests`;
  }
};
```

## Part 4: Guardrails & Safety

### Guardrail 1: File Whitelist

Agent can only modify approved files:

```javascript
const APPROVED_DIRS = [
  '/src/api',
  '/src/components',
  '/src/utils'
];

const PROTECTED_FILES = [
  'package.json',
  '.env.example',
  'CLAUDE.md'
];

function canModify(filePath) {
  if (PROTECTED_FILES.some(f => filePath.includes(f))) {
    return false;
  }
  return APPROVED_DIRS.some(dir => filePath.startsWith(dir));
}
```

### Guardrail 2: Change Limits

Agent doesn't modify too many files at once:

```javascript
const MAX_FILES_PER_RUN = 10;
const MAX_LINES_CHANGED = 500;

function validateChanges(changes) {
  if (changes.length > MAX_FILES_PER_RUN) {
    throw new Error(`Too many files: ${changes.length}`);
  }

  const totalLines = changes.reduce((sum, c) => sum + c.additions + c.deletions, 0);
  if (totalLines > MAX_LINES_CHANGED) {
    throw new Error(`Too many changes: ${totalLines} lines`);
  }

  return true;
}
```

### Guardrail 3: Approval Gates

Dangerous operations require approval:

```javascript
async function requireApproval(action) {
  const dangerous = [
    'DELETE',
    'MIGRATE_DATABASE',
    'UPDATE_DEPENDENCIES',
    'DEPLOY'
  ];

  if (dangerous.includes(action.type)) {
    console.log(`Waiting for approval: ${action.description}`);
    // In production: send approval request to human
    // For now: wait for user confirmation
    return await askUser('Approve this action?');
  }

  return true;
}
```

### Guardrail 4: Rollback Capability

Agent saves state to rollback if needed:

```javascript
async function createCheckpoint() {
  const timestamp = new Date().toISOString();
  const checkpointDir = `.checkpoints/${timestamp}`;

  // Save current state
  await exec(`git commit -m "Checkpoint before agent run"`);
  await exec(`git tag checkpoint-${timestamp}`);

  return checkpointDir;
}

async function rollback(checkpointId) {
  await exec(`git reset --hard ${checkpointId}`);
  await exec(`git clean -fd`);
  console.log(`Rolled back to ${checkpointId}`);
}
```

## Part 5: Monitoring & Logging

### Structured Logging

```javascript
class AgentLogger {
  log(level, message, context = {}) {
    const entry = {
      timestamp: new Date().toISOString(),
      level,
      message,
      context
    };
    console.log(JSON.stringify(entry));
    this.logFile.append(JSON.stringify(entry) + '\n');
  }

  info(msg, ctx) { this.log('INFO', msg, ctx); }
  warn(msg, ctx) { this.log('WARN', msg, ctx); }
  error(msg, ctx) { this.log('ERROR', msg, ctx); }
}
```

### Progress Reporting

```javascript
class ProgressTracker {
  constructor(totalSteps) {
    this.total = totalSteps;
    this.completed = 0;
    this.failures = [];
  }

  completeStep(name) {
    this.completed++;
    const percent = (this.completed / this.total * 100).toFixed(0);
    console.log(`[${percent}%] Completed: ${name}`);
  }

  recordFailure(step, error) {
    this.failures.push({ step, error });
  }

  report() {
    return {
      completed: this.completed,
      total: this.total,
      percent: (this.completed / this.total * 100).toFixed(0),
      failures: this.failures
    };
  }
}
```

## Part 6: Cost Management

Autonomous agents can be expensive. Control costs:

### Budget Limits

```javascript
class Agent {
  constructor(tokenBudget = 10000) {
    this.tokenBudget = tokenBudget;
    this.tokensUsed = 0;
  }

  async ask(prompt) {
    const estimate = estimateTokens(prompt);
    if (this.tokensUsed + estimate > this.tokenBudget) {
      throw new Error(`Exceeded token budget`);
    }

    const response = await askClaude(prompt);
    this.tokensUsed += countActualTokens(response);
    return response;
  }
}
```

### Smart Batching

Instead of asking Claude per file, batch requests:

```javascript
// ❌ Expensive: 10 separate requests
for (const file of files) {
  await askClaude(`Refactor ${file}`);
}

// ✅ Cheaper: 1 batch request
await askClaude(`
  Refactor these 10 files with the same pattern:
  ${files.join(', ')}

  Show the pattern once, then apply to all files.
`);
```

## Part 7: Testing Autonomous Agents

### Test 1: Happy Path

```javascript
describe('DeployAgent', () => {
  it('deploys successfully with no errors', async () => {
    const agent = new DeployAgent({ dryRun: true });
    const result = await agent.run();

    expect(result.success).toBe(true);
    expect(result.deployed).toBe(true);
  });
});
```

### Test 2: Error Recovery

```javascript
it('recovers from transient errors', async () => {
  const agent = new Agent({
    maxRetries: 3,
    retryDelay: 100 // Fast for testing
  });

  // Simulate failure then success
  let attempts = 0;
  mockTask.mockImplementationOnce(() => {
    attempts++;
    if (attempts === 1) throw new Error('Temporary failure');
    return { success: true };
  });

  const result = await agent.run();
  expect(result.recovered).toBe(true);
  expect(attempts).toBe(2);
});
```

### Test 3: Guardrails

```javascript
it('refuses to modify protected files', async () => {
  const agent = new Agent();
  expect(() => agent.modifyFile('package.json')).toThrow();
  expect(() => agent.modifyFile('.env')).toThrow();
});
```

## Part 8: Production Considerations

### Running in CI/CD

```yaml
# .github/workflows/agent.yml
name: Autonomous Agent
on: [workflow_dispatch]

jobs:
  agent:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: npm ci
      - run: node agent.js
        env:
          AGENT_TOKEN_BUDGET: 20000
          AGENT_APPROVAL_REQUIRED: 'DELETE,DEPLOY'
      - uses: actions/upload-artifact@v3
        with:
          name: agent-report
          path: agent-report.json
```

### Notification & Alerts

```javascript
async function notifyResult(result) {
  if (result.success) {
    await sendSlack(`✓ Agent completed: ${result.summary}`);
  } else {
    await sendSlack(`✗ Agent failed: ${result.error}`);
    await sendEmail(admin@company.com, 'Agent Failure', result.error);
  }
}
```

## Checklist: Autonomous Agent Ready

- ✓ Clear goal definition and success criteria
- ✓ Task breakdown into manageable steps
- ✓ Execution engine with error handling
- ✓ Verification/testing at each step
- ✓ Error recovery and retry logic
- ✓ Guardrails (file whitelist, limits, approvals)
- ✓ Rollback capability
- ✓ Structured logging and monitoring
- ✓ Cost/token budget management
- ✓ Production safety (CI/CD, notifications)

Autonomous agents extend your development capacity—when built right, they're reliable force multipliers.
