---
skill_name: AI Cost Optimization
description: Reduce LLM costs through token budgeting, caching, model routing, and batch processing
category: AI/LLM
version: 1.0.0
---

# AI Cost Optimization

## Overview
LLM costs add up fast. Token counting, smart caching, and model routing reduce bills by 50-80% without sacrificing quality.

## Token Counting & Budgeting

### Token Estimation

```python
import tiktoken

def count_tokens(text: str, model: str = "gpt-4") -> int:
    """Count tokens for a given model"""

    encoding = tiktoken.encoding_for_model(model)
    tokens = encoding.encode(text)
    return len(tokens)

def estimate_cost(
    prompt_tokens: int,
    completion_tokens: int,
    model: str = "gpt-4-turbo"
) -> dict:
    """Estimate API cost for a single request"""

    pricing = {
        "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},  # per 1K tokens
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-4-turbo": {"input": 0.01, "output": 0.03},
        "gpt-4o": {"input": 0.005, "output": 0.015},
    }

    rates = pricing.get(model, pricing["gpt-4"])

    input_cost = (prompt_tokens / 1000) * rates["input"]
    output_cost = (completion_tokens / 1000) * rates["output"]
    total_cost = input_cost + output_cost

    return {
        "input_tokens": prompt_tokens,
        "output_tokens": completion_tokens,
        "input_cost": input_cost,
        "output_cost": output_cost,
        "total_cost": total_cost
    }

# Example
prompt = "Explain quantum computing in 100 words"
prompt_tokens = count_tokens(prompt)
estimated_completion = 100  # ~75 tokens

cost = estimate_cost(prompt_tokens, estimated_completion, "gpt-4")
print(f"Estimated cost: ${cost['total_cost']:.4f}")
```

### Token Budgeting System

```python
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class TokenBudget:
    daily_limit: int
    monthly_limit: int
    daily_used: int = 0
    monthly_used: int = 0
    last_reset: datetime = None

    def reset_if_needed(self):
        """Reset daily budget at midnight"""
        if self.last_reset is None or datetime.now().date() != self.last_reset.date():
            self.daily_used = 0
            self.last_reset = datetime.now()

    def can_afford(self, tokens: int) -> bool:
        """Check if request fits in budget"""
        self.reset_if_needed()
        return (self.daily_used + tokens < self.daily_limit and
                self.monthly_used + tokens < self.monthly_limit)

    def use_tokens(self, tokens: int):
        """Track token usage"""
        self.reset_if_needed()
        self.daily_used += tokens
        self.monthly_used += tokens

# Usage
budget = TokenBudget(daily_limit=100000, monthly_limit=2000000)

def query_with_budget(prompt: str) -> str:
    """Query LLM only if within budget"""
    from openai import OpenAI
    client = OpenAI()

    tokens_needed = count_tokens(prompt) + 500  # Estimate output

    if not budget.can_afford(tokens_needed):
        return "Budget exceeded for today"

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )

    actual_tokens = response.usage.prompt_tokens + response.usage.completion_tokens
    budget.use_tokens(actual_tokens)

    return response.choices[0].message.content
```

## Prompt Optimization

### Remove Redundancy

```
❌ VERBOSE (850 tokens):
You are an AI assistant designed to help users with various tasks.
Your primary goal is to provide accurate, helpful, and informative responses.
You should always consider the context of the question and provide responses
that are relevant to the user's needs. Please be concise but thorough...

✓ CONCISE (120 tokens):
You are a helpful AI assistant. Be accurate, relevant, and concise.
```

```python
def optimize_system_prompt(system_prompt: str) -> tuple[str, float]:
    """
    Suggest optimizations to system prompt.
    Returns optimized prompt and token savings %.
    """

    original_tokens = count_tokens(system_prompt)

    # Remove common redundancies
    optimized = system_prompt
    removals = [
        "Please", "Thank you",
        "I appreciate", "As an AI",
        "It is important to note that",
        "You should always",
    ]

    for phrase in removals:
        optimized = optimized.replace(phrase, "").strip()

    # Remove extra whitespace
    optimized = " ".join(optimized.split())

    new_tokens = count_tokens(optimized)
    savings = (original_tokens - new_tokens) / original_tokens * 100

    return optimized, savings
```

## Model Routing (Intelligent Model Selection)

```python
from openai import OpenAI

client = OpenAI()

def route_to_optimal_model(
    prompt: str,
    task_type: str
) -> str:
    """
    Route requests to the most cost-effective model for the task.
    """

    prompt_tokens = count_tokens(prompt)

    routing_rules = {
        "classification": {
            "model": "gpt-3.5-turbo",  # 90% accuracy, 10x cheaper
            "max_tokens": 100
        },
        "summarization": {
            "model": "gpt-3.5-turbo",
            "max_tokens": 300
        },
        "reasoning": {
            "model": "gpt-4",  # Need stronger reasoning
            "max_tokens": 1000
        },
        "code_generation": {
            "model": "gpt-4",
            "max_tokens": 2000
        },
        "creative_writing": {
            "model": "gpt-3.5-turbo",
            "max_tokens": 1500
        }
    }

    config = routing_rules.get(task_type, routing_rules["reasoning"])

    response = client.chat.completions.create(
        model=config["model"],
        messages=[{"role": "user", "content": prompt}],
        max_tokens=config["max_tokens"]
    )

    return response.choices[0].message.content

# Usage
response = route_to_optimal_model(
    "Classify this sentiment: 'Great product!'",
    task_type="classification"
)  # Uses gpt-3.5-turbo (10x cheaper than gpt-4)
```

## Caching Strategies

### Prompt Caching with LangChain

```python
from langchain.globals import set_llm_cache
from langchain.cache import InMemoryCache

# Enable in-memory cache
set_llm_cache(InMemoryCache())

from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4", cache=InMemoryCache())

# First call: hits API
response1 = llm.invoke("What is quantum computing?")

# Second call with identical prompt: served from cache
response2 = llm.invoke("What is quantum computing?")

print(f"First call: API hit")
print(f"Second call: Cached (instant, no cost)")
```

### Redis Caching for Production

```python
import redis
import json
import hashlib

class RedisPromptCache:
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_client = redis.from_url(redis_url)

    def _hash_prompt(self, prompt: str) -> str:
        """Create cache key from prompt"""
        return hashlib.sha256(prompt.encode()).hexdigest()

    def get(self, prompt: str) -> dict | None:
        """Retrieve cached response"""
        key = self._hash_prompt(prompt)
        cached = self.redis_client.get(key)
        if cached:
            return json.loads(cached)
        return None

    def set(self, prompt: str, response: dict, ttl_hours: int = 24):
        """Cache response"""
        key = self._hash_prompt(prompt)
        self.redis_client.setex(
            key,
            int(ttl_hours * 3600),
            json.dumps(response)
        )

cache = RedisPromptCache()

def cached_query(prompt: str) -> str:
    """Query with caching"""
    from openai import OpenAI
    client = OpenAI()

    # Check cache first
    cached_response = cache.get(prompt)
    if cached_response:
        return cached_response["content"]

    # Call API
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )

    result = response.choices[0].message.content

    # Cache for future requests
    cache.set(prompt, {"content": result})

    return result
```

## Batch Processing

### Batch API (OpenAI)

```python
import json
from openai import OpenAI

client = OpenAI()

def create_batch_job(prompts: list) -> str:
    """
    Send multiple requests in one batch.
    Batch API: 50% cheaper, processes in 24 hours.
    """

    requests = []
    for i, prompt in enumerate(prompts):
        requests.append({
            "custom_id": f"request-{i}",
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": "gpt-4-turbo",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 200
            }
        })

    # Save to JSONL
    with open("batch_requests.jsonl", "w") as f:
        for req in requests:
            f.write(json.dumps(req) + "\n")

    # Submit batch
    with open("batch_requests.jsonl", "rb") as f:
        batch_job = client.beta.batches.create(
            input_file=f,
            endpoint="/v1/chat/completions"
        )

    return batch_job.id

def get_batch_results(batch_id: str) -> list:
    """Retrieve batch results"""
    batch_job = client.beta.batches.retrieve(batch_id)

    if batch_job.status == "completed":
        results = client.beta.batches.results(batch_id)
        return list(results)

    return []
```

## Quantization & Distillation

```python
# Use smaller models where possible
model_comparison = {
    "GPT-4 Turbo": {"cost": 1.0, "quality": 1.0, "speed": 0.7},
    "GPT-4": {"cost": 0.33, "quality": 0.95, "speed": 0.8},
    "GPT-3.5 Turbo": {"cost": 0.033, "quality": 0.80, "speed": 1.0},
    "Llama 2": {"cost": 0.001, "quality": 0.70, "speed": 0.9},  # Open source
}

# Decision rule: Use smallest model that achieves required quality
def select_model_by_quality_threshold(required_quality: float) -> str:
    """Select cheapest model meeting quality requirement"""
    for model, metrics in sorted(
        model_comparison.items(),
        key=lambda x: x[1]["cost"]
    ):
        if metrics["quality"] >= required_quality:
            return model
    return "GPT-4 Turbo"
```

## Production Checklist

- [ ] Implement token counting before API calls
- [ ] Set daily/monthly token budgets
- [ ] Optimize system prompts (remove redundancy)
- [ ] Use model routing for cost-aware selection
- [ ] Enable prompt caching for repeated queries
- [ ] Use Batch API for non-urgent requests (50% savings)
- [ ] Monitor per-request costs continuously
- [ ] A/B test cheaper models on subset of traffic
- [ ] Implement request deduplication
- [ ] Use streaming for long responses (count tokens accurately)
- [ ] Document cost per feature/use case
- [ ] Set cost alerts for unusual spending
