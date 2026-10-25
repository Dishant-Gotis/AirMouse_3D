---
skill_name: api-integration-patterns
description: API integration patterns for OAuth flows, token refresh, rate limit queuing, and retry strategies
category: Workflow Automation
version: 1.0.0
---

# API Integration Patterns

## Overview
Robust API integration requires careful handling of authentication, rate limits, and failures. This guide covers production patterns.

## Pattern 1: OAuth 2.0 Flow

**Authorize third-party API access securely**

```javascript
async function initiateOAuthFlow(service, userId) {
  // Generate state (prevents CSRF)
  const state = generateRandomString(32);
  await storeState(state, userId);

  // Build authorization URL
  const params = new URLSearchParams({
    client_id: process.env[`${service}_CLIENT_ID`],
    redirect_uri: `${appUrl}/oauth/callback`,
    response_type: 'code',
    scope: process.env[`${service}_SCOPES`],
    state: state
  });

  const authUrl = `https://${service}/oauth/authorize?${params}`;

  return { authUrl };
}

async function handleOAuthCallback(code, state) {
  // Validate state
  const userId = await getStoredState(state);
  if (!userId) throw new Error('Invalid state');

  // Exchange code for token
  const tokenResponse = await fetch(`https://${service}/oauth/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      client_id: process.env[`${service}_CLIENT_ID`],
      client_secret: process.env[`${service}_CLIENT_SECRET`],
      code: code,
      grant_type: 'authorization_code',
      redirect_uri: `${appUrl}/oauth/callback`
    })
  });

  const tokens = await tokenResponse.json();

  // Store securely (encrypted)
  await storeTokens(userId, {
    accessToken: tokens.access_token,
    refreshToken: tokens.refresh_token,
    expiresAt: Date.now() + tokens.expires_in * 1000
  });

  return { success: true };
}
```

## Pattern 2: Token Refresh

**Auto-refresh expired tokens**

```javascript
async function getValidToken(userId, service) {
  let tokens = await getStoredTokens(userId, service);

  // Check if expired
  if (tokens.expiresAt < Date.now()) {
    // Refresh token
    const refreshResponse = await fetch(`https://${service}/oauth/token`, {
      method: 'POST',
      body: JSON.stringify({
        client_id: process.env[`${service}_CLIENT_ID`],
        client_secret: process.env[`${service}_CLIENT_SECRET`],
        refresh_token: tokens.refreshToken,
        grant_type: 'refresh_token'
      })
    });

    const newTokens = await refreshResponse.json();

    // Update stored tokens
    tokens = {
      accessToken: newTokens.access_token,
      refreshToken: newTokens.refresh_token,
      expiresAt: Date.now() + newTokens.expires_in * 1000
    };

    await storeTokens(userId, tokens);
  }

  return tokens.accessToken;
}

async function apiCall(userId, service, endpoint, options = {}) {
  const token = await getValidToken(userId, service);

  return fetch(`https://${service}/api${endpoint}`, {
    ...options,
    headers: {
      ...options.headers,
      'Authorization': `Bearer ${token}`
    }
  });
}
```

## Pattern 3: Rate Limit Queuing

**Queue requests to avoid hitting rate limits**

```javascript
class RateLimitQueue {
  constructor(maxRequestsPerSecond = 10) {
    this.maxRequests = maxRequestsPerSecond;
    this.requests = [];
    this.queue = [];
  }

  async add(fn) {
    return new Promise((resolve, reject) => {
      this.queue.push({ fn, resolve, reject });
      this.process();
    });
  }

  async process() {
    // Check if we can execute
    const now = Date.now();

    // Remove old requests (older than 1 second)
    this.requests = this.requests.filter(t => now - t < 1000);

    // If under limit, execute
    if (this.requests.length < this.maxRequests && this.queue.length > 0) {
      const { fn, resolve, reject } = this.queue.shift();

      try {
        const result = await fn();
        this.requests.push(Date.now());
        resolve(result);
      } catch (error) {
        reject(error);
      }

      this.process();
    } else if (this.queue.length > 0) {
      // Wait before trying again
      setTimeout(() => this.process(), 100);
    }
  }
}

// Usage
const queue = new RateLimitQueue(5); // 5 requests per second

// Queue many requests
const results = await Promise.all([
  queue.add(() => fetch('/api/users/1')),
  queue.add(() => fetch('/api/users/2')),
  queue.add(() => fetch('/api/users/3')),
  // ... more requests
]);
```

## Pattern 4: Exponential Backoff Retry

**Intelligent retry with backoff**

```javascript
async function apiCallWithRetry(
  fn,
  maxAttempts = 5,
  initialDelay = 100
) {
  let lastError;

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await fn();

    } catch (error) {
      lastError = error;

      const isRetryable = [408, 429, 500, 502, 503, 504].includes(
        error.statusCode
      );

      if (!isRetryable || attempt === maxAttempts) {
        throw error;
      }

      // Exponential backoff with jitter
      const delay = initialDelay * Math.pow(2, attempt - 1);
      const jitter = Math.random() * delay * 0.1;
      const totalDelay = delay + jitter;

      console.log(
        `Attempt ${attempt} failed. Retrying in ${totalDelay}ms`
      );

      await new Promise(resolve => setTimeout(resolve, totalDelay));
    }
  }

  throw lastError;
}

// Usage
const data = await apiCallWithRetry(() =>
  fetch('/api/data')
    .then(r => r.status === 200 ? r.json() : Promise.reject(r))
);
```

## Pattern 5: Request/Response Caching

**Cache API responses to reduce calls**

```javascript
class APICache {
  constructor(ttl = 5 * 60 * 1000) {
    this.cache = new Map();
    this.ttl = ttl;
  }

  async get(key, fetcher) {
    // Check cache
    const cached = this.cache.get(key);
    if (cached && cached.expiresAt > Date.now()) {
      return cached.data;
    }

    // Fetch fresh
    const data = await fetcher();

    // Store in cache
    this.cache.set(key, {
      data,
      expiresAt: Date.now() + this.ttl
    });

    return data;
  }

  invalidate(key) {
    this.cache.delete(key);
  }

  invalidatePattern(pattern) {
    for (const key of this.cache.keys()) {
      if (key.match(pattern)) {
        this.cache.delete(key);
      }
    }
  }
}

// Usage
const cache = new APICache(5 * 60 * 1000); // 5 min cache

const userList = await cache.get('users:list', async () => {
  return fetch('/api/users').then(r => r.json());
});

// Invalidate when user is created
cache.invalidate('users:list');
```

## Best Practices

1. **Secure credentials** — Use environment variables
2. **Validate responses** — Check status and schema
3. **Handle rate limits gracefully** — Queue and backoff
4. **Cache aggressively** — Reduce API calls
5. **Implement timeouts** — Don't wait forever
6. **Log all calls** — Debugging and audit
7. **Monitor quota** — Alert before limits
8. **Test integration** — With sandbox APIs
9. **Document auth** — Team needs to know
10. **Rotate secrets** — Regular credential refresh

