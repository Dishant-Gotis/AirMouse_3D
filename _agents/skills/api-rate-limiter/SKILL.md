---
skill_name: api-rate-limiter
description: Implement rate limiting with algorithms, Redis backends, and edge deployment
category: Developer Tools
version: 1.0.0
---

# API Rate Limiter: Algorithms, Implementation, and Deployment

This skill teaches how to implement effective rate limiting for APIs. Learn algorithm selection, backend choices, client handling, and production deployment patterns.

## Part 1: Rate Limiting Algorithms

### Algorithm 1: Token Bucket

**How it works:**
- Bucket holds N tokens
- Each request costs 1 token
- Tokens refill at fixed rate (e.g., 100 tokens/minute)
- Request allowed if tokens available

**Visual:**
```
Bucket capacity: 10 tokens
Refill rate: 2 tokens/second

Time 0:  Bucket=[10/10] Request → Allow, Bucket=[9/10]
Time 0.5: Bucket=[10/10] (refilled)
Time 0.6: Bucket=[10/10] Request → Allow, Bucket=[9/10]
Time 0.7: Bucket=[9.8/10] Request → Reject (queued)
```

**Use cases:** Bursty traffic, mobile clients, generous limits
**Pros:** Allows burst traffic, smooth
**Cons:** Can deplete quota quickly

### Algorithm 2: Sliding Window Log

**How it works:**
- Keep log of request timestamps
- For each request, count requests in last N seconds
- Allow if count < limit

**Visual:**
```
Window: 60 seconds, Limit: 5 requests

[10:00:05] Request 1 ✓ → Log: [10:00:05]
[10:00:10] Request 2 ✓ → Log: [10:00:05, 10:00:10]
[10:00:12] Request 3 ✓ → Log: [10:00:05, 10:00:10, 10:00:12]
[10:00:15] Request 4 ✓ → Log: [..., 10:00:15]
[10:00:18] Request 5 ✓ → Log: [..., 10:00:18]
[10:00:20] Request 6 ✗ → Reject (5 in last 60s)
[10:01:06] Request 7 ✓ → Log updated (10:00:05 outside window)
```

**Use cases:** Strict rate limiting, fair sharing
**Pros:** Accurate, fair
**Cons:** Memory intensive (stores timestamps)

### Algorithm 3: Sliding Window Counter (Fixed Window + Overflow)

**How it works:**
- Divide time into fixed buckets
- Track requests in current + previous bucket
- Pro-rate previous bucket to account for window overlap

**Formula:**
```
Requests allowed = Limit - (Prev_bucket_requests * Overlap_ratio)
```

**Use cases:** Balanced accuracy and memory
**Pros:** Less memory than log, more accurate than fixed
**Cons:** Slightly complex

### Algorithm 4: Leaky Bucket

**How it works:**
- Requests flow into bucket at varying rate
- Leak out at constant rate (process queue)
- Reject if bucket full

**Visual:**
```
Bucket (capacity=5)
          ↓ Requests (in)
    ┌─────────────┐
    │ ░ ░ ░ ░ ░   │  (5 requests queued)
    └─────────────┘
          ↓ Fixed rate (out)
     Process queue
```

**Use cases:** Smoothing traffic, fairness
**Pros:** Smooth output, predictable
**Cons:** Rejects bursts, longer latency

## Part 2: Redis-Based Rate Limiter (Sliding Window)

### Implementation Pattern

```typescript
import { createClient } from 'redis';

const redis = createClient();

async function rateLimit(key: string, limit: number, windowSeconds: number): Promise<boolean> {
  const now = Date.now();
  const windowStart = now - (windowSeconds * 1000);

  // Remove entries outside the window
  await redis.zremrangebyscore(key, '-inf', windowStart);

  // Count requests in current window
  const count = await redis.zcard(key);

  if (count >= limit) {
    return false; // Rate limit exceeded
  }

  // Add current request
  await redis.zadd(key, { score: now, member: `${now}-${Math.random()}` });

  // Set expiry (window + buffer)
  await redis.expire(key, windowSeconds + 1);

  return true;
}

// Usage
const allowed = await rateLimit(`user:${userId}:api`, 100, 60); // 100 req/min
if (!allowed) {
  throw new Error('Rate limit exceeded');
}
```

**Why Sorted Sets?**
- Score = timestamp
- Automatic range queries (find timestamps in window)
- Fast deletion (zremrangebyscore)

### Token Bucket with Redis

```typescript
async function tokenBucket(key: string, capacity: number, refillRate: number): Promise<boolean> {
  const now = Date.now();
  const bucket = await redis.hgetall(key);

  const tokens = bucket.tokens ? Number(bucket.tokens) : capacity;
  const lastRefill = bucket.lastRefill ? Number(bucket.lastRefill) : now;

  // Calculate elapsed seconds
  const elapsedSeconds = (now - lastRefill) / 1000;
  const tokensToAdd = elapsedSeconds * refillRate;
  const newTokens = Math.min(tokens + tokensToAdd, capacity);

  if (newTokens < 1) {
    return false; // No tokens available
  }

  // Update bucket
  await redis.hset(key, {
    tokens: newTokens - 1,
    lastRefill: now
  });
  await redis.expire(key, 3600); // 1 hour TTL

  return true;
}
```

### Upstash Rate Limit (Serverless-Friendly)

```typescript
import { Ratelimit } from "@upstash/ratelimit";
import { Redis } from "@upstash/redis";

const redis = new Redis({
  url: process.env.UPSTASH_REDIS_REST_URL,
  token: process.env.UPSTASH_REDIS_REST_TOKEN,
});

const ratelimit = new Ratelimit({
  redis: redis,
  limiter: Ratelimit.slidingWindow(10, "10 s"), // 10 req per 10 seconds
});

export async function handler(request: Request) {
  const ip = request.headers.get("x-forwarded-for") || "anonymous";
  const { success } = await ratelimit.limit(ip);

  if (!success) {
    return new Response("Rate limited", { status: 429 });
  }

  return new Response("OK");
}
```

## Part 3: Edge Runtime Rate Limiting (Cloudflare/Vercel)

### Cloudflare Workers

```typescript
export default {
  async fetch(request: Request, env: Env) {
    const ip = request.headers.get('cf-connecting-ip') || 'unknown';
    const key = new Request(request.url, { method: 'GET' });
    const cache = caches.default;

    // Check cache for rate limit counter
    let count = 0;
    const cached = await cache.match(key);
    if (cached) {
      count = Number(cached.text());
    }

    if (count >= 100) {
      return new Response('Rate limited', { status: 429 });
    }

    // Increment counter
    count++;
    const response = new Response(count.toString());
    response.headers.set('Cache-Control', 'max-age=60'); // Window: 60 seconds
    await cache.put(key, response);

    return new Response('OK');
  }
};
```

### Vercel Edge Middleware

```typescript
import { NextRequest, NextResponse } from 'next/server';

const limiter = new Map<string, { count: number; reset: number }>();

export function middleware(request: NextRequest) {
  const ip = request.ip || 'unknown';
  const now = Date.now();
  const record = limiter.get(ip) || { count: 0, reset: now + 60000 };

  if (now > record.reset) {
    record.count = 1;
    record.reset = now + 60000;
  } else {
    record.count++;
  }

  limiter.set(ip, record);

  if (record.count > 100) {
    return NextResponse.json(
      { error: 'Rate limited' },
      { status: 429, headers: {
        'X-RateLimit-Limit': '100',
        'X-RateLimit-Remaining': '0',
        'X-RateLimit-Reset': String(record.reset)
      }}
    );
  }

  return NextResponse.next();
}

export const config = {
  matcher: '/api/:path*',
};
```

## Part 4: User Identification Strategies

### Strategy 1: IP-Based

```typescript
// Simple but imperfect (shared IPs, VPNs, proxies)
const ip = request.headers.get('x-forwarded-for') ||
           request.headers.get('x-real-ip') ||
           request.socket.remoteAddress;

const rateLimitKey = `rate:ip:${ip}`;
```

### Strategy 2: API Key

```typescript
// Reliable for known clients
const apiKey = request.headers.get('x-api-key');
if (!apiKey) {
  return new Response('Missing API key', { status: 401 });
}

const rateLimitKey = `rate:key:${apiKey}`;
```

### Strategy 3: JWT Subject

```typescript
// For authenticated users
const token = request.headers.get('authorization')?.split(' ')[1];
const decoded = jwt.verify(token, SECRET);

const rateLimitKey = `rate:user:${decoded.sub}`;
```

### Strategy 4: Composite Key

```typescript
// Combination: user + feature + time window
const userId = decoded?.sub || 'anonymous';
const feature = 'search';
const hour = Math.floor(Date.now() / 3600000);

const rateLimitKey = `rate:${userId}:${feature}:${hour}`;
```

## Part 5: Response Headers and Standards

### Standard Headers

```
X-RateLimit-Limit: 100          # Total limit
X-RateLimit-Remaining: 42       # Requests left
X-RateLimit-Reset: 1614556800   # Unix timestamp when limit resets
Retry-After: 60                 # Seconds to wait before retrying
```

### Implementation

```typescript
const response = {
  'X-RateLimit-Limit': String(limit),
  'X-RateLimit-Remaining': String(Math.max(0, limit - count)),
  'X-RateLimit-Reset': String(Math.ceil(resetTime / 1000)),
};

if (count >= limit) {
  response['Retry-After'] = String(Math.ceil((resetTime - now) / 1000));
  return new Response('Rate limited', {
    status: 429,
    headers: response
  });
}

return new Response('OK', { headers: response });
```

## Part 6: Client-Side Exponential Backoff

### Implementation with Jitter

```typescript
async function fetchWithBackoff(url: string, maxRetries = 5) {
  let retries = 0;

  while (retries < maxRetries) {
    try {
      const response = await fetch(url);

      if (response.status === 429) {
        const retryAfter = response.headers.get('Retry-After');
        const delay = retryAfter ?
          parseInt(retryAfter) * 1000 :
          Math.pow(2, retries) * 1000 + Math.random() * 1000; // Exponential + jitter

        console.log(`Rate limited. Retrying in ${delay}ms`);
        await new Promise(r => setTimeout(r, delay));
        retries++;
        continue;
      }

      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return response;
    } catch (error) {
      if (retries < maxRetries - 1) {
        const delay = Math.pow(2, retries) * 1000 + Math.random() * 1000;
        await new Promise(r => setTimeout(r, delay));
        retries++;
      } else {
        throw error;
      }
    }
  }
}
```

## Part 7: Multi-Tier Rate Limiting

### Example: Per-Second, Per-Minute, Per-Day

```typescript
async function multiTierRateLimit(userId: string) {
  const limits = [
    { key: `rate:${userId}:sec`, limit: 10, window: 1 },
    { key: `rate:${userId}:min`, limit: 100, window: 60 },
    { key: `rate:${userId}:day`, limit: 10000, window: 86400 },
  ];

  for (const tier of limits) {
    const allowed = await rateLimit(tier.key, tier.limit, tier.window);
    if (!allowed) {
      return {
        allowed: false,
        tier: tier.key,
        resetTime: await getResetTime(tier.key)
      };
    }
  }

  return { allowed: true };
}
```

## Part 8: Testing Rate Limits

### Load Testing Pattern

```bash
# Using Apache Bench
ab -n 200 -c 10 https://api.example.com/endpoint

# Using hey
hey -n 200 -c 10 https://api.example.com/endpoint
```

### Programmatic Test

```typescript
async function testRateLimiting() {
  const requests = Array(150).fill(null).map((_, i) =>
    fetch('/api/endpoint', {
      headers: { 'x-user-id': 'test-user' }
    })
  );

  const responses = await Promise.all(requests);
  const successCount = responses.filter(r => r.status === 200).length;
  const rateLimitedCount = responses.filter(r => r.status === 429).length;

  console.log(`Success: ${successCount}, Rate Limited: ${rateLimitedCount}`);
  // Expected: ~100 success, ~50 rate limited
}
```

## Part 9: Graceful Degradation

### Soft Limits (Warning)

```typescript
const count = await getRequestCount(userId);
const limit = 100;

if (count > limit * 0.8) { // 80% of limit
  response.headers.set('X-RateLimit-Warning', 'Approaching limit');
}
```

### Queueing vs Rejection

```typescript
async function handleRequest(request: Request) {
  const allowed = await rateLimit(key, limit, window);

  if (!allowed) {
    // Option 1: Queue (better UX)
    await queue.push({
      request,
      timestamp: Date.now(),
      userId
    });
    return { queued: true, position: queue.length };

    // Option 2: Reject (simpler)
    // return new Response('Rate limited', { status: 429 });
  }

  return processRequest(request);
}
```

## Checklist: Rate Limiting Production Ready

- ✓ Algorithm chosen (token bucket recommended)
- ✓ Redis backend deployed with failover
- ✓ User identification strategy defined
- ✓ Response headers implemented
- ✓ Client exponential backoff configured
- ✓ Multi-tier limits (per-second, per-minute, per-day)
- ✓ Monitoring and alerting set up
- ✓ Load testing completed
- ✓ Graceful degradation for overload
- ✓ Documentation for API consumers

Rate limiting is about fairness and stability, not punishment.
