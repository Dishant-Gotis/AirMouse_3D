---
skill_name: ai-product-builder
description: Build AI-powered products with architecture patterns, evaluation frameworks, and safety practices
category: AI & LLM
version: 1.0.0
---

# AI Product Builder: From Concept to Production

This skill teaches how to design, build, and deploy AI-powered products. Learn architecture patterns, evaluation strategies, cost optimization, and safety practices for production-grade AI systems.

## Part 1: AI Product Types

### Type 1: Chatbot / Q&A

**Architecture:** LLM + optional retrieval
**Examples:** Customer support bots, help desk assistants
**Key challenge:** Staying in domain, accurate answers

```
User Input → Retrieve context (optional) → LLM → Response
```

### Type 2: Copilot (Autocomplete)

**Architecture:** LLM + streaming + partial output
**Examples:** Code completion, email suggestions
**Key challenge:** Fast latency (<500ms), relevant suggestions

### Type 3: Autonomous Agent

**Architecture:** LLM + tools + loop
**Examples:** Research agents, automation bots
**Key challenge:** Avoiding infinite loops, tool safety

```
Goal → LLM (choose tool) → Execute tool → Update state → Loop until done
```

### Type 4: Data Pipeline / Batch

**Architecture:** LLM + bulk processing
**Examples:** Content classification, data extraction
**Key challenge:** Consistency, cost per item

### Type 5: Content Generator

**Architecture:** LLM + templates + quality control
**Examples:** Marketing copy, blog posts, ad creative
**Key challenge:** Brand voice, fact-checking

## Part 2: Architecture Patterns

### Pattern 1: Direct API Call

**Simplest approach:**
```typescript
const response = await claude.message({
  model: "claude-3-5-sonnet-20241022",
  messages: [{ role: "user", content: userInput }]
});
```

**When to use:** Low-latency requirements, simple prompts
**Limitations:** No context beyond prompt, no memory

### Pattern 2: Retrieval-Augmented Generation (RAG)

```
User Query → Search Knowledge Base → Retrieve relevant docs
                          ↓
                    LLM (with context)
                          ↓
                       Response
```

**Implementation:**
```typescript
async function ragResponse(userQuery: string) {
  // 1. Search knowledge base
  const context = await searchDocs(userQuery);

  // 2. Augment prompt
  const augmentedPrompt = `
    Context: ${context}
    Question: ${userQuery}
    Provide an answer based on the context above.
  `;

  // 3. Call LLM
  const response = await claude.message({
    messages: [{ role: "user", content: augmentedPrompt }]
  });

  return response;
}
```

**When to use:** Knowledge-heavy products, internal docs
**Tradeoff:** More latency (+retrieval time), higher accuracy

### Pattern 3: Tool-Calling Agents

```
LLM analyzes request → Chooses best tool(s) → Execute → Loop
```

**Example: Research Agent**
```typescript
const tools = [
  {
    name: "search_web",
    description: "Search the web for information",
    input_schema: { query: "string" }
  },
  {
    name: "analyze_sentiment",
    description: "Analyze sentiment of text",
    input_schema: { text: "string" }
  }
];

async function agentLoop(goal: string) {
  let messages = [
    { role: "user", content: `Goal: ${goal}` }
  ];

  while (true) {
    const response = await claude.message({
      tools,
      messages
    });

    if (response.stop_reason === "end_turn") {
      return response.content[0].text;
    }

    // Process tool uses
    for (const block of response.content) {
      if (block.type === "tool_use") {
        const result = await executeTool(block.name, block.input);
        messages.push({
          role: "user",
          content: [{
            type: "tool_result",
            tool_use_id: block.id,
            content: JSON.stringify(result)
          }]
        });
      }
    }

    messages.push({ role: "assistant", content: response.content });
  }
}
```

**When to use:** Complex tasks requiring multiple steps
**Tradeoff:** Multiple API calls, loops add latency

### Pattern 4: Fine-Tuned Models

**When to consider:**
- Specific domain with domain-specific language
- High volume (millions of inferences)
- Cost critical (fine-tuned = cheaper inference)

**Process:**
```
1. Collect 100+ training examples
2. Format as prompt-completion pairs
3. Fine-tune on API
4. Evaluate on test set
5. Deploy fine-tuned model
```

## Part 3: Evaluation Framework

### Metric 1: Accuracy (Task Completion)

```typescript
function evaluateAccuracy(outputs: string[], goldStandard: string[]) {
  const matches = outputs.filter((o, i) => o === goldStandard[i]).length;
  return matches / outputs.length;
}

// Example: Classification task
const predictions = ["spam", "ham", "spam"];
const ground_truth = ["spam", "ham", "ham"];
const accuracy = evaluateAccuracy(predictions, ground_truth); // 0.67
```

**Measurement:**
- Exact match (too strict)
- Fuzzy match (allows typos)
- Semantic similarity (using embeddings)

### Metric 2: Quality (Human-Like)

**BLEU Score** (for text generation):
```
Measures: How many n-grams match reference text
Range: 0-1 (higher is better)
Limitation: Doesn't capture meaning, only surface patterns
```

**ROUGE Score** (for summarization):
```
Measures: Overlap between generated and reference summary
Types: ROUGE-1 (unigram), ROUGE-2 (bigram), ROUGE-L (longest common subsequence)
```

**METEOR Score** (better than BLEU):
```
Accounts for synonyms, paraphrases, word order
Better correlation with human judgment
```

### Metric 3: Latency

```typescript
async function benchmarkLatency(requests: number) {
  const times: number[] = [];

  for (let i = 0; i < requests; i++) {
    const start = performance.now();
    await claude.message({ messages });
    times.push(performance.now() - start);
  }

  const p50 = percentile(times, 0.5);
  const p95 = percentile(times, 0.95);
  const p99 = percentile(times, 0.99);

  console.log({ p50, p95, p99 });
}
```

**Target latencies:**
- Chatbot: <2 seconds acceptable
- Copilot: <500ms acceptable
- Batch: minutes to hours acceptable

### Metric 4: Cost per Inference

```typescript
function calculateCost(inputTokens: number, outputTokens: number) {
  // Claude 3.5 Sonnet pricing
  const inputCost = (inputTokens / 1_000_000) * 3; // $3 per 1M
  const outputCost = (outputTokens / 1_000_000) * 15; // $15 per 1M
  return inputCost + outputCost;
}

// Example: Classify 1000 documents
const costPerItem = calculateCost(500, 50); // ~$0.00081
const totalCost = costPerItem * 1000; // ~$0.81
```

### Human Evaluation

```typescript
interface EvalResult {
  correctness: 1 | 2 | 3 | 4 | 5; // 1=wrong, 5=correct
  helpfulness: 1 | 2 | 3 | 4 | 5; // 1=not helpful, 5=very helpful
  clarity: 1 | 2 | 3 | 4 | 5; // 1=unclear, 5=very clear
  length: "too short" | "appropriate" | "too long";
}

// Evaluate 30-50 examples with humans
// Calculate inter-rater agreement (Cohen's kappa)
// Average scores
```

## Part 4: Prompt Management

### Version Control Prompts

```
prompts/
├── v1/
│   ├── system.md
│   ├── examples.md
│   └── metadata.json (model, temperature, max_tokens)
├── v2/
│   ├── system.md
│   └── metadata.json
└── v3/
    └── system.md (current)
```

**metadata.json:**
```json
{
  "version": "v3",
  "created_at": "2024-03-15",
  "model": "claude-3-5-sonnet-20241022",
  "temperature": 0.7,
  "max_tokens": 1024,
  "performance": {
    "accuracy": 0.92,
    "latency_p95": 1250,
    "cost_per_inference": 0.00123
  }
}
```

### A/B Testing Prompts

```typescript
async function abTestPrompts(testQueries: string[]) {
  const results = {
    v2: [],
    v3: []
  };

  for (const query of testQueries) {
    // Test v2
    const response2 = await claude.message({
      system: loadPrompt('v2/system.md'),
      messages: [{ role: "user", content: query }]
    });
    results.v2.push(response2);

    // Test v3
    const response3 = await claude.message({
      system: loadPrompt('v3/system.md'),
      messages: [{ role: "user", content: query }]
    });
    results.v3.push(response3);
  }

  // Compare quality metrics
  const v2Quality = evaluate(results.v2, goldStandard);
  const v3Quality = evaluate(results.v3, goldStandard);

  console.log(`v2: ${v2Quality}, v3: ${v3Quality}`);
  // Ship winner
}
```

## Part 5: Latency Optimization

### Strategy 1: Streaming

```typescript
const stream = await claude.message({
  stream: true,
  messages: [...]
});

for await (const event of stream) {
  if (event.type === 'content_block_delta') {
    console.log(event.delta.text); // Print as it comes
  }
}
```

**Benefit:** User sees response starting immediately
**Tradeoff:** Can't measure full response before returning

### Strategy 2: Parallel Tool Calls

```typescript
// Get all tools needed first
const tools = [
  { name: "fetch_user", input: { id: 123 } },
  { name: "fetch_orders", input: { userId: 123 } },
  { name: "fetch_reviews", input: { userId: 123 } }
];

// Execute in parallel, not sequentially
const results = await Promise.all(
  tools.map(t => executeTool(t.name, t.input))
);
```

### Strategy 3: Caching + Batch

```typescript
// Cache expensive computations
const cache = new Map<string, string>();

async function cachedInference(prompt: string) {
  if (cache.has(prompt)) {
    return cache.get(prompt);
  }

  const response = await claude.message({ messages: [{ role: "user", content: prompt }] });
  cache.set(prompt, response);
  return response;
}

// Batch similar requests
const batchQuery = `
Classify these 10 reviews:
${reviews.map((r, i) => `${i+1}. "${r}"`).join('\n')}

Return JSON: [{ id: number, category: string }]
`;
```

### Strategy 4: Smaller Model for Routing

```typescript
async function intelligentRouting(input: string) {
  // Use fast, cheap model to decide
  const routing = await claude.message({
    model: "claude-3-haiku-20240307", // Faster, cheaper
    messages: [{
      role: "user",
      content: `Route to: search, calculate, or chat\nInput: ${input}`
    }]
  });

  const route = routing.content[0].text;

  // Use appropriate handler
  if (route.includes("search")) {
    return await handleSearch(input);
  } else if (route.includes("calculate")) {
    return await handleCalculate(input);
  } else {
    return await handleChat(input);
  }
}
```

## Part 6: Safety and Validation

### Output Validation

```typescript
async function generateAndValidate(prompt: string): Promise<string> {
  const response = await claude.message({
    messages: [{ role: "user", content: prompt }]
  });

  const output = response.content[0].text;

  // Validation checks
  if (!isValidJSON(output)) throw new Error("Invalid JSON");
  if (containsBannedContent(output)) throw new Error("Banned content");
  if (isTooLong(output)) throw new Error("Output too long");

  return output;
}

// Validators
function isValidJSON(text: string): boolean {
  try {
    JSON.parse(text);
    return true;
  } catch {
    return false;
  }
}

function containsBannedContent(text: string): boolean {
  return text.match(/banned_word/i) !== null;
}

function isTooLong(text: string): boolean {
  return text.length > 10000;
}
```

### Hallucination Detection

```typescript
async function detectHallucination(
  claim: string,
  supportingDocs: string[]
): Promise<boolean> {
  const response = await claude.message({
    messages: [{
      role: "user",
      content: `
Is this claim supported by the documents?
Claim: "${claim}"

Supporting documents:
${supportingDocs.map((d, i) => `${i+1}. ${d}`).join('\n')}

Respond: "Yes" or "No" only.
`
    }]
  });

  return response.content[0].text.includes("No");
}
```

## Part 7: Monitoring and Observability

### Track Key Metrics

```typescript
interface InferenceEvent {
  id: string;
  timestamp: number;
  inputTokens: number;
  outputTokens: number;
  latency: number;
  cost: number;
  model: string;
  success: boolean;
  errorMessage?: string;
}

async function logInference(event: InferenceEvent) {
  await database.inferences.create(event);

  // Aggregate to Datadog/New Relic
  await metrics.gauge('ai_latency_p95', calculateP95(lastHour()));
  await metrics.counter('ai_errors', { count: errorCount });
  await metrics.gauge('ai_cost_daily', calculateDailyCost());
}
```

### Cost Monitoring

```typescript
async function checkDailyCostBudget() {
  const spent = await calculateSpentToday();
  const budget = 100; // $100/day

  if (spent > budget * 0.8) {
    await sendAlert(`AI cost at 80% of daily budget: $${spent}`);
  }

  if (spent > budget) {
    await disableNonCriticalFeatures();
    await sendCriticalAlert(`AI cost exceeded daily budget`);
  }
}
```

## Part 8: Deployment Checklist

- ✓ Evaluated on test set (>30 examples)
- ✓ Latency acceptable for use case
- ✓ Cost per inference calculated
- ✓ Error handling implemented
- ✓ Fallback behavior defined
- ✓ Output validation in place
- ✓ Monitoring dashboards set up
- ✓ Cost alerts configured
- ✓ User feedback collection active
- ✓ Rate limiting implemented
- ✓ Audit logging enabled

AI products need care and feeding. Monitor continuously.
