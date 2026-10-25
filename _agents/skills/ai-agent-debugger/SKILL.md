---
skill_name: ai-agent-debugger
description: Debug agent loops by detecting infinite loops, hallucination patterns, cost runaway, token waste, and context degradation
category: AI & Claude Code Mastery
version: 1.0.0
---

# AI Agent Debugger: Diagnose & Fix Agent Issues

Master debugging techniques for AI agents. Learn to detect hallucinations, infinite loops, cost explosions, and token wastage. Turn broken agents into reliable systems.

## Part 1: Common Agent Failure Modes

### Failure Mode 1: Infinite Loops

**Symptom**: Agent keeps asking the same question or repeating the same action

```
Iteration 1: "Create user endpoint"
Claude: "Created POST /api/users"
Iteration 2: "Create user endpoint" (same prompt!)
Claude: "Created POST /api/users"
Iteration 3: ... (infinite repeat)
```

**Root Cause**: Agent not advancing state or checking completion

**Fix**:
```typescript
function preventInfiniteLoops(agent: Agent) {
  const seen = new Set();

  return async (step: Step) => {
    const stepHash = hash(step.action + step.prompt);

    if (seen.has(stepHash)) {
      console.error(`Loop detected: ${step.action}`);
      return { success: false, reason: 'Infinite loop' };
    }

    seen.add(stepHash);
    return await agent.executeStep(step);
  };
}
```

### Failure Mode 2: Hallucination Cascade

**Symptom**: Agent generates plausible-sounding but incorrect code

```
Agent: "I'll use the .map2() method on this array"
Reality: JavaScript arrays don't have .map2()
Agent builds on this hallucination: "Then chain .filter2()"
Result: Entire feature is fabricated
```

**Root Cause**: Agent confident in incorrect assumptions

**Fix**:
```typescript
async function verifyBeforeBuilding(claim: string): boolean {
  // Don't just trust the agent—verify
  const checks = [
    methodExists(claim), // Does this method exist?
    syntaxValid(claim),  // Is syntax correct?
    fileExists(claim),   // Does file exist?
    dependencyInstalled(claim) // Is package installed?
  ];

  return checks.every(c => c === true);
}

async function buildWithVerification(feature: string) {
  // Generate code
  const code = await agent.generate(feature);

  // Before executing: verify every claim
  const claims = extractClaims(code);
  for (const claim of claims) {
    if (!verifyBeforeBuilding(claim)) {
      console.error(`Unverified claim: ${claim}`);
      // Ask agent to fix
      return await agent.fixHallucination(claim);
    }
  }

  // Only then execute
  return await execute(code);
}
```

### Failure Mode 3: Cost Runaway

**Symptom**: Token usage spirals out of control

```
Request 1: 1,000 tokens → $0.01
Request 2: 5,000 tokens → $0.05
Request 3: 50,000 tokens → $0.50
Request 4: 100,000 tokens → $1.00
Total: $1.56 for a task that should cost $0.10
```

**Root Cause**: Context window grows with each iteration

**Fix**:
```typescript
class BudgetedAgent {
  private tokenBudget = 10000;
  private tokensUsed = 0;

  async ask(prompt: string): Promise<string> {
    const estimated = estimateTokens(prompt);

    if (this.tokensUsed + estimated > this.tokenBudget) {
      console.error(`Token budget exceeded: ${this.tokensUsed + estimated} > ${this.tokenBudget}`);
      throw new Error('Budget exhausted');
    }

    const response = await claude.ask(prompt);
    this.tokensUsed += countTokens(response);

    return response;
  }

  async askWithContext(prompt: string, context: string[]) {
    // Instead of including all context, summarize
    const summary = await this.summarizeContext(context);
    const trimmed = summary.slice(0, 500); // Max 500 tokens for context

    return await this.ask(`${trimmed}\n\n${prompt}`);
  }

  private async summarizeContext(context: string[]): Promise<string> {
    // One request to summarize, then reuse summary
    if (this.contextSummary) return this.contextSummary;

    this.contextSummary = await claude.ask(
      `Summarize in 200 tokens: ${context.join('\n')}`
    );
    return this.contextSummary;
  }
}
```

### Failure Mode 4: Context Degradation

**Symptom**: Agent forgets key constraints in later iterations

```
Iteration 1: "Create API endpoint using Express"
Iteration 5: "Now create the same endpoint using FastAPI"
Iteration 10: "I'll use plain HTTP—no framework"
(Agent forgot original Express requirement)
```

**Root Cause**: Context lost as conversation grows

**Fix**:
```typescript
class ContextPreserver {
  private systemPrompt = '';
  private invariants = [];

  setSystemPrompt(prompt: string) {
    this.systemPrompt = prompt;
  }

  addInvariant(rule: string) {
    this.invariants.push(rule);
  }

  buildPrompt(userPrompt: string): string {
    const invariantSection = this.invariants.length > 0
      ? `\n\nIMPORTANT RULES (ALWAYS FOLLOW):\n${this.invariants.join('\n')}`
      : '';

    return `${this.systemPrompt}${invariantSection}\n\n${userPrompt}`;
  }
}

// Usage
const agent = new ContextPreserver();
agent.setSystemPrompt('You are building an Express API...');
agent.addInvariant('Always use TypeScript strict mode');
agent.addInvariant('Never use var—only const/let');
agent.addInvariant('All API routes must validate input with Zod');

// Every request includes these rules
const prompt = agent.buildPrompt('Generate the user endpoint');
```

## Part 2: Debugging Instrumentation

### Instrumentation 1: Action Logging

```typescript
class InstrumentedAgent {
  private log: Array<{
    action: string;
    input: any;
    output: any;
    timestamp: Date;
    tokensUsed: number;
  }> = [];

  async executeAction(action: string, input: any) {
    const startTime = Date.now();
    console.log(`[${action}] Starting...`);

    try {
      const output = await performAction(action, input);
      const elapsed = Date.now() - startTime;

      this.log.push({
        action,
        input,
        output,
        timestamp: new Date(),
        tokensUsed: countTokens(output)
      });

      console.log(`[${action}] ✓ Completed in ${elapsed}ms`);
      return output;
    } catch (error) {
      console.error(`[${action}] ✗ Failed: ${error.message}`);
      throw error;
    }
  }

  exportLog() {
    return this.log.map(entry => ({
      ...entry,
      timestamp: entry.timestamp.toISOString()
    }));
  }
}
```

### Instrumentation 2: State Tracking

```typescript
class StatefulAgent {
  private state: Record<string, any> = {};
  private stateHistory: Array<Record<string, any>> = [];

  setState(key: string, value: any) {
    console.log(`[STATE] ${key} = ${JSON.stringify(value).slice(0, 100)}`);
    this.state[key] = value;
    this.stateHistory.push({ ...this.state, timestamp: new Date() });
  }

  getState(key: string) {
    return this.state[key];
  }

  detectStateRegression() {
    // Alert if state goes backward unexpectedly
    for (let i = 1; i < this.stateHistory.length; i++) {
      const prev = this.stateHistory[i - 1];
      const curr = this.stateHistory[i];

      for (const key in prev) {
        if (typeof prev[key] === 'number' && curr[key] < prev[key]) {
          console.warn(`[REGRESSION] ${key} decreased: ${prev[key]} → ${curr[key]}`);
        }
      }
    }
  }
}
```

### Instrumentation 3: Metric Collection

```typescript
class MetricsCollector {
  private metrics = {
    totalIterations: 0,
    successfulSteps: 0,
    failedSteps: 0,
    totalTokensUsed: 0,
    totalCost: 0,
    averageTimePerStep: 0,
    hallucinations: []
  };

  recordStep(success: boolean, tokens: number, timeMs: number) {
    this.metrics.totalIterations++;
    if (success) {
      this.metrics.successfulSteps++;
    } else {
      this.metrics.failedSteps++;
    }
    this.metrics.totalTokensUsed += tokens;
    this.metrics.totalCost = this.metrics.totalTokensUsed * 0.000015; // Approximate
  }

  recordHallucination(claim: string, reality: string) {
    this.metrics.hallucinations.push({
      claimed: claim,
      actual: reality,
      timestamp: new Date()
    });
  }

  report() {
    const successRate = (
      this.metrics.successfulSteps / this.metrics.totalIterations * 100
    ).toFixed(1);

    return `
      Total Iterations: ${this.metrics.totalIterations}
      Success Rate: ${successRate}%
      Tokens Used: ${this.metrics.totalTokensUsed.toLocaleString()}
      Estimated Cost: $${this.metrics.totalCost.toFixed(2)}
      Hallucinations Found: ${this.metrics.hallucinations.length}
    `;
  }
}
```

## Part 3: Debugging Checklist

When an agent fails, run through this checklist:

```markdown
## Agent Failure Debugging

### Symptom Analysis
- [ ] Is agent stuck in a loop? (same action repeatedly)
- [ ] Is agent hallucinating? (claiming things that don't exist)
- [ ] Is cost spiraling? (tokens growing exponentially)
- [ ] Is context lost? (forgetting earlier rules)
- [ ] Is performance degrading? (iterations taking longer)

### Data Collection
- [ ] Export agent logs
- [ ] Review action sequence
- [ ] Check token usage per iteration
- [ ] List all claims agent made
- [ ] Verify each claim against reality

### Diagnosis
- [ ] Where did it first deviate from expected behavior?
- [ ] What prompt change triggered the failure?
- [ ] Which model/settings were used?
- [ ] What was the context window size?

### Fix
- [ ] Simplify the goal (break into smaller steps)
- [ ] Add explicit verification steps
- [ ] Reduce context (summarize old info)
- [ ] Add budget limits
- [ ] Use more constrained model (Haiku instead of Opus)
- [ ] Add explicit guardrails
```

## Part 4: Debugging Tools

### Tool 1: Prompt Replay

```typescript
class PromptReplayer {
  async replay(agent: Agent, logs: ActionLog[]) {
    for (const log of logs) {
      console.log(`\nReplaying: ${log.action}`);
      console.log(`Input: ${JSON.stringify(log.input)}`);
      console.log(`Original output: ${log.output.slice(0, 200)}...`);

      // Re-run with current agent
      const newOutput = await agent.executeAction(log.action, log.input);
      console.log(`New output: ${newOutput.slice(0, 200)}...`);

      // Compare
      if (newOutput !== log.output) {
        console.warn('Output changed! Agent behavior may have shifted.');
      }
    }
  }
}
```

### Tool 2: Cost Analyzer

```typescript
function analyzeTokenCost(logs: ActionLog[]) {
  const costByAction = {};
  const costByIteration = {};

  for (const log of logs) {
    const tokens = log.output.split(/\s+/).length * 1.3; // Rough estimate
    const cost = tokens * 0.000015;

    if (!costByAction[log.action]) costByAction[log.action] = 0;
    costByAction[log.action] += cost;

    if (!costByIteration[log.iteration]) costByIteration[log.iteration] = 0;
    costByIteration[log.iteration] += cost;
  }

  console.log('Cost by action:');
  Object.entries(costByAction)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5)
    .forEach(([action, cost]) => {
      console.log(`  ${action}: $${cost.toFixed(2)}`);
    });

  // Detect runaway
  const iterations = Object.values(costByIteration) as number[];
  for (let i = 1; i < iterations.length; i++) {
    if (iterations[i] > iterations[i - 1] * 2) {
      console.warn(`Cost spike at iteration ${i}: ${iterations[i].toFixed(2)}`);
    }
  }
}
```

### Tool 3: Hallucination Detector

```typescript
async function detectHallucinations(code: string, fs: FileSystem) {
  const hallucinations = [];

  // Pattern 1: Methods that don't exist
  const methodCalls = code.match(/\.\w+\(/g) || [];
  for (const call of methodCalls) {
    const method = call.slice(1, -1);
    if (!isValidMethod(method)) {
      hallucinations.push(`Non-existent method: ${method}`);
    }
  }

  // Pattern 2: Imports that don't exist
  const imports = code.match(/import .* from '.*'/g) || [];
  for (const imp of imports) {
    const moduleName = imp.match(/'(.*)'/)?.[1];
    if (!fs.moduleExists(moduleName)) {
      hallucinations.push(`Non-existent module: ${moduleName}`);
    }
  }

  // Pattern 3: Class methods on wrong types
  const assignments = code.match(/const \w+ = .*/g) || [];
  for (const assign of assignments) {
    const [left, right] = assign.split('=');
    const type = inferType(right);
    // Check if methods called on this type are valid
  }

  return hallucinations;
}
```

## Part 5: Recovery Patterns

### Pattern 1: Graceful Degradation

```typescript
async function executeWithGracefulDegradation(task: Task) {
  try {
    // Try full solution first
    return await agent.executeFullTask(task);
  } catch (error) {
    console.warn(`Full task failed: ${error.message}`);

    // Fall back to simpler approach
    console.log('Falling back to simplified approach...');
    return await agent.executeSimplifiedTask(task);
  }
}
```

### Pattern 2: Checkpoint Recovery

```typescript
async function executeWithCheckpoints(task: Task) {
  const checkpoints = [];

  for (let i = 0; i < task.steps.length; i++) {
    try {
      const result = await agent.executeStep(task.steps[i]);
      checkpoints.push({ step: i, result, success: true });
    } catch (error) {
      console.error(`Step ${i} failed. Rolling back to checkpoint ${i - 1}`);

      const lastGood = checkpoints[i - 1];
      agent.restoreCheckpoint(lastGood);

      // Retry with simplified version
      const simplified = simplifyStep(task.steps[i]);
      const retryResult = await agent.executeStep(simplified);
      checkpoints.push({ step: i, result: retryResult, success: true });
    }
  }

  return checkpoints;
}
```

### Pattern 3: Human-in-the-Loop Recovery

```typescript
async function executeWithHumanFallback(task: Task) {
  let attempts = 0;
  const maxAttempts = 3;

  while (attempts < maxAttempts) {
    try {
      return await agent.executeTask(task);
    } catch (error) {
      attempts++;

      if (attempts < maxAttempts) {
        console.log(`Attempt ${attempts} failed. Retrying...`);
        // Automatically retry with modified prompt
        task.prompt = await improvePrompt(task.prompt);
      } else {
        // Give up, ask human
        console.error('All automatic attempts failed.');
        console.log('Task context:', await exportTaskContext(task));
        throw new Error('Human intervention required');
      }
    }
  }
}
```

## Checklist: Agent Debugger Ready

- ✓ Recognize common failure modes (loops, hallucinations, runaway)
- ✓ Add instrumentation (logging, state tracking, metrics)
- ✓ Detect cost spirals before they happen
- ✓ Verify agent claims against reality
- ✓ Preserve context with system prompts and invariants
- ✓ Run debugging checklist on failures
- ✓ Use replay and analysis tools
- ✓ Implement graceful degradation
- ✓ Set up checkpoint recovery
- ✓ Plan human fallback paths

Well-instrumented agents fail fast, cost less, and require fewer iterations to get right.
