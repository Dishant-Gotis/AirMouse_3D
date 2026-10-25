---
skill_name: API Rate Limiting Design
description: Implement rate limiting with token bucket, leaky bucket, and sliding window algorithms for distributed systems
category: API & Integration
version: 1.0.0
---

# API Rate Limiting Design

## Overview
Rate limiting protects APIs from abuse. Master algorithms and distributed implementations for fair usage control.

## Token Bucket Algorithm

```python
import time
from threading import Lock

class TokenBucket:
    def __init__(self, capacity, refill_rate):
        self.capacity = capacity
        self.refill_rate = refill_rate  # tokens per second
        self.tokens = capacity
        self.last_refill = time.time()
        self.lock = Lock()

    def allow_request(self, tokens=1):
        with self.lock:
            self._refill()

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    def _refill(self):
        now = time.time()
        elapsed = now - self.last_refill
        new_tokens = elapsed * self.refill_rate

        self.tokens = min(self.capacity, self.tokens + new_tokens)
        self.last_refill = now

class RateLimiter:
    def __init__(self):
        self.buckets = {}

    def is_allowed(self, user_id, limit=100, window=60):
        """Check if request is allowed (100 requests per 60 seconds)"""
        if user_id not in self.buckets:
            self.buckets[user_id] = TokenBucket(limit, limit / window)

        return self.buckets[user_id].allow_request()
```

## Sliding Window Algorithm

```python
from collections import deque
import time

class SlidingWindowCounter:
    def __init__(self, max_requests, window_seconds):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = deque()

    def is_allowed(self):
        now = time.time()

        # Remove old requests outside window
        while self.requests and self.requests[0] <= now - self.window_seconds:
            self.requests.popleft()

        if len(self.requests) < self.max_requests:
            self.requests.append(now)
            return True

        return False
```

## Distributed Rate Limiting with Redis

```python
import redis
import json

class RedisRateLimiter:
    def __init__(self, redis_host='localhost', redis_port=6379):
        self.redis = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)

    def is_allowed(self, user_id, limit=100, window=60):
        """Token bucket in Redis"""
        key = f"rate_limit:{user_id}"

        # Get current bucket state
        data = self.redis.get(key)

        if not data:
            # Initialize bucket
            bucket = {
                'tokens': limit,
                'last_refill': time.time()
            }
        else:
            bucket = json.loads(data)
            # Refill tokens
            elapsed = time.time() - bucket['last_refill']
            bucket['tokens'] = min(limit, bucket['tokens'] + elapsed * (limit / window))
            bucket['last_refill'] = time.time()

        # Check if request allowed
        if bucket['tokens'] >= 1:
            bucket['tokens'] -= 1
            self.redis.setex(key, window, json.dumps(bucket))
            return True

        self.redis.setex(key, window, json.dumps(bucket))
        return False

    def get_remaining(self, user_id):
        """Get remaining tokens"""
        key = f"rate_limit:{user_id}"
        data = self.redis.get(key)

        if not data:
            return 100  # Default limit

        bucket = json.loads(data)
        return max(0, int(bucket['tokens']))
```

## Flask Rate Limiting Middleware

```python
from flask import Flask, request, jsonify
from functools import wraps
import time

app = Flask(__name__)
rate_limiter = RedisRateLimiter()

def rate_limit(limit=100, window=60):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            user_id = request.remote_addr
            if request.user:
                user_id = request.user.id

            if not rate_limiter.is_allowed(user_id, limit, window):
                remaining = rate_limiter.get_remaining(user_id)
                response = jsonify({
                    'error': 'rate_limit_exceeded',
                    'limit': limit,
                    'window': window,
                    'retry_after': window
                })
                response.status_code = 429
                response.headers['Retry-After'] = str(window)
                response.headers['X-RateLimit-Limit'] = str(limit)
                response.headers['X-RateLimit-Remaining'] = '0'
                return response

            remaining = rate_limiter.get_remaining(user_id)
            response = f(*args, **kwargs)

            # Add rate limit headers
            if isinstance(response, tuple):
                body, status_code = response
                response = (body, status_code, {
                    'X-RateLimit-Limit': str(limit),
                    'X-RateLimit-Remaining': str(remaining),
                    'X-RateLimit-Reset': str(int(time.time()) + window)
                })

            return response
        return wrapper
    return decorator

@app.route('/api/users', methods=['GET'])
@rate_limit(limit=100, window=60)
def get_users():
    return jsonify([])
```

## Tiered Rate Limits

```python
class TieredRateLimiter:
    TIER_LIMITS = {
        'free': {'requests': 100, 'window': 3600},      # 100 req/hour
        'pro': {'requests': 10000, 'window': 3600},     # 10K req/hour
        'enterprise': {'requests': float('inf'), 'window': 3600}  # Unlimited
    }

    def __init__(self, redis_client):
        self.redis = redis_client

    def is_allowed(self, user_id, tier='free'):
        limits = self.TIER_LIMITS.get(tier, self.TIER_LIMITS['free'])

        key = f"rate_limit:{tier}:{user_id}"
        current = self.redis.incr(key)

        if current == 1:
            self.redis.expire(key, limits['window'])

        return current <= limits['requests']

    def get_usage(self, user_id, tier='free'):
        limits = self.TIER_LIMITS.get(tier, self.TIER_LIMITS['free'])
        key = f"rate_limit:{tier}:{user_id}"
        current = self.redis.get(key) or 0

        return {
            'limit': limits['requests'],
            'used': int(current),
            'remaining': max(0, limits['requests'] - int(current)),
            'reset_in': self.redis.ttl(key)
        }
```

## Response Headers

```python
def add_rate_limit_headers(response, limit, remaining, reset):
    response.headers['X-RateLimit-Limit'] = str(limit)
    response.headers['X-RateLimit-Remaining'] = str(remaining)
    response.headers['X-RateLimit-Reset'] = str(reset)
    return response

# When rate limited
def rate_limit_exceeded(retry_after):
    response = jsonify({
        'error': 'rate_limit_exceeded',
        'message': 'Too many requests'
    })
    response.status_code = 429
    response.headers['Retry-After'] = str(retry_after)
    return response
```

## Production Checklist

- [ ] Choose appropriate algorithm (token bucket recommended)
- [ ] Use Redis for distributed systems
- [ ] Implement tiered limits by user type
- [ ] Return 429 when limit exceeded
- [ ] Include Retry-After header
- [ ] Add X-RateLimit headers to responses
- [ ] Monitor rate limit violations
- [ ] Allow burst capacity
- [ ] Document rate limits in API docs
- [ ] Test under load
