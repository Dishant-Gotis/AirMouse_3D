---
skill_name: api-gateway-implementation
description: Building API gateways - routing, authentication, rate limiting, circuit breaking, middleware
category: [backend, advanced]
version: 1.0.0
---

# API Gateway Implementation

## Architecture Overview

An API gateway is the single entry point for client requests, handling:
- **Routing**: Direct requests to correct backend services
- **Authentication**: Validate credentials before forwarding
- **Rate limiting**: Prevent abuse and ensure fair usage
- **Circuit breaking**: Handle failing services gracefully
- **Load balancing**: Distribute load across service instances

```
┌─────────┐
│ Client  │
└────┬────┘
     │
     ↓
┌─────────────────────┐
│   API Gateway       │
│ ┌─────────────────┐ │
│ │  Auth/JWT       │ │
│ │  Rate Limit     │ │
│ │  Circuit Break  │ │
│ │  Load Balance   │ │
│ └─────────────────┘ │
└──┬──────┬──────┬────┘
   │      │      │
   ↓      ↓      ↓
 [User]  [Post] [Comment]
Services
```

## Basic Gateway Implementation

```javascript
const express = require('express');
const httpProxy = require('express-http-proxy');
const jwt = require('jsonwebtoken');
const rateLimit = require('express-rate-limit');

const app = express();

// Rate limiting middleware
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // limit each IP to 100 requests per windowMs
  message: 'Too many requests from this IP'
});

// Authentication middleware
const authMiddleware = (req, res, next) => {
  const token = req.headers.authorization?.split(' ')[1];

  if (!token) {
    return res.status(401).json({ error: 'No token provided' });
  }

  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    req.user = decoded;
    next();
  } catch (err) {
    res.status(401).json({ error: 'Invalid token' });
  }
};

// Apply global middleware
app.use(limiter);
app.use(authMiddleware);

// Route to user service
app.use('/users', httpProxy('http://user-service:3001', {
  proxyReqPathResolver: (req) => {
    return '/api' + req.originalUrl;
  }
}));

// Route to post service
app.use('/posts', httpProxy('http://post-service:3002', {
  proxyReqPathResolver: (req) => {
    return '/api' + req.originalUrl;
  }
}));

app.listen(3000);
```

## Circuit Breaker Pattern

Prevent cascading failures by stopping requests to failing services:

```javascript
const CircuitBreaker = require('opossum');

const breaker = new CircuitBreaker(async (url) => {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`${response.status}`);
  return response.json();
}, {
  timeout: 3000, // 3 second timeout
  errorThresholdPercentage: 50, // Trip after 50% failures
  resetTimeout: 30000, // Try again after 30 seconds
  rollingCountTimeout: 10000, // Count errors over 10 seconds
});

breaker.on('open', () => {
  console.log('Circuit breaker opened');
});

breaker.on('halfOpen', () => {
  console.log('Circuit breaker half-open, testing...');
});

app.get('/users/:id', async (req, res) => {
  try {
    const user = await breaker.fire(`http://user-service:3001/users/${req.params.id}`);
    res.json(user);
  } catch (err) {
    if (breaker.opened) {
      return res.status(503).json({ error: 'Service unavailable' });
    }
    res.status(500).json({ error: err.message });
  }
});
```

## Advanced Rate Limiting

```javascript
const RedisStore = require('rate-limit-redis');
const redis = require('redis');
const client = redis.createClient();

// Rate limit per user
const userLimiter = rateLimit({
  store: new RedisStore({
    client: client,
    prefix: 'rl:user:'
  }),
  keyGenerator: (req) => req.user?.id || req.ip,
  skip: (req) => req.user?.tier === 'premium', // Premium users unlimited
  windowMs: 60 * 1000, // 1 minute
  max: (req) => req.user?.tier === 'pro' ? 1000 : 100
});

// Rate limit per endpoint
const apiLimiter = rateLimit({
  store: new RedisStore({
    client: client,
    prefix: 'rl:api:'
  }),
  keyGenerator: (req) => `${req.user?.id}:${req.method}:${req.path}`,
  windowMs: 60 * 1000,
  max: 50,
  skip: (req) => req.path === '/health' // Exempt health checks
});

app.use('/api/', userLimiter);
app.use('/api/', apiLimiter);

// Dynamic rate limiting based on user tier
app.use((req, res, next) => {
  const tier = req.user?.tier;
  const limits = {
    'free': 100,
    'pro': 1000,
    'enterprise': 100000
  };

  req.rateLimit = limits[tier] || limits.free;
  next();
});
```

## Middleware Chain Pattern

```javascript
class GatewayMiddleware {
  constructor() {
    this.middlewares = [];
  }

  use(name, fn) {
    this.middlewares.push({ name, fn });
    return this;
  }

  async execute(req, res, next) {
    let index = 0;

    const proceed = async () => {
      if (index >= this.middlewares.length) {
        return next();
      }

      const { name, fn } = this.middlewares[index++];
      console.log(`Executing: ${name}`);

      try {
        await fn(req, res, proceed);
      } catch (err) {
        console.error(`Error in ${name}:`, err);
        throw err;
      }
    };

    await proceed();
  }
}

const gateway = new GatewayMiddleware();

gateway
  .use('auth', authMiddleware)
  .use('rateLimit', rateLimitMiddleware)
  .use('requestId', (req, res, next) => {
    req.id = require('uuid').v4();
    res.setHeader('X-Request-ID', req.id);
    next();
  })
  .use('logging', (req, res, next) => {
    console.log(`[${req.id}] ${req.method} ${req.path}`);
    next();
  })
  .use('bodyParser', express.json())
  .use('routing', (req, res, next) => {
    // Route to backend services
    next();
  });

app.use((req, res, next) => {
  gateway.execute(req, res, next).catch(err => {
    res.status(500).json({ error: err.message });
  });
});
```

## Service Mesh Integration

```javascript
// Kong API Gateway configuration
const adminApi = 'http://localhost:8001';

async function registerService() {
  // Register upstream service
  await fetch(`${adminApi}/upstreams`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      name: 'user-service',
      algorithm: 'round-robin',
      healthchecks: {
        active: {
          http_path: '/health',
          interval: 60
        }
      }
    })
  });

  // Add targets
  await fetch(`${adminApi}/upstreams/user-service/targets`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      target: 'user-service-1:3001',
      weight: 100
    })
  });

  // Create route
  await fetch(`${adminApi}/routes`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      paths: ['/users'],
      service: { name: 'user-service' }
    })
  });

  // Add rate limiting plugin
  await fetch(`${adminApi}/routes/users/plugins`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      name: 'rate-limiting',
      config: {
        minute: 100,
        hour: 10000
      }
    })
  });
}
```

## Request/Response Transformation

```javascript
class RequestTransformer {
  static async transform(req) {
    return {
      ...req,
      headers: {
        ...req.headers,
        'X-Forwarded-For': req.ip,
        'X-Original-URL': req.originalUrl,
        'X-Request-ID': req.id
      }
    };
  }
}

class ResponseTransformer {
  static transform(data, statusCode) {
    return {
      success: statusCode < 400,
      status: statusCode,
      data: data,
      timestamp: new Date().toISOString()
    };
  }
}

app.use(async (req, res, next) => {
  const originalJson = res.json;

  res.json = function(data) {
    const transformed = ResponseTransformer.transform(
      data,
      res.statusCode
    );
    return originalJson.call(this, transformed);
  };

  next();
});
```

## Health Checks and Monitoring

```javascript
const healthChecks = new Map();

function registerHealthCheck(name, fn) {
  healthChecks.set(name, fn);
}

app.get('/health', async (req, res) => {
  const results = {};
  let allHealthy = true;

  for (const [name, check] of healthChecks) {
    try {
      const status = await check();
      results[name] = { status: 'ok', ...status };
    } catch (err) {
      results[name] = { status: 'down', error: err.message };
      allHealthy = false;
    }
  }

  res.status(allHealthy ? 200 : 503).json({
    status: allHealthy ? 'healthy' : 'degraded',
    checks: results
  });
});

// Register service checks
registerHealthCheck('user-service', async () => {
  const response = await fetch('http://user-service:3001/health');
  return { responseTime: response.headers.get('x-response-time') };
});

registerHealthCheck('database', async () => {
  const result = await db.query('SELECT 1');
  return { latency: result.duration };
});
```

## Key Takeaways

- **Single entry point**: All client requests route through gateway
- **Circuit breaker**: Stop requests to failing services, recover gracefully
- **Rate limiting**: Prevent abuse, ensure fair resource allocation
- **Middleware chain**: Apply auth, logging, transformation sequentially
- **Health monitoring**: Track upstream service health
- **Service discovery**: Dynamically route to available instances
