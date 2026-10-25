---
skill_name: api-security-hardening
description: Secure REST APIs with authentication, authorization, input validation, rate limiting, and WAF rules
category: Security & Compliance
version: 1.0.0
---

# API Security Hardening

APIs are attack targets. Implement defense-in-depth: authentication, authorization, input validation, rate limiting, and monitoring.

## API Authentication

### API Key Management
```python
# Generate API key (random, non-predictable)
import secrets
api_key = secrets.token_urlsafe(32)  # 256-bit random key
api_key_hash = bcrypt.hashpw(api_key.encode(), bcrypt.gensalt())

# Store hash, return key once
db.create_api_key(user_id, api_key_hash, label='Production')

# Client sends in header
curl -H "X-API-Key: sk_live_49d1cd688f4a8..." https://api.example.com/data

# Server validates
@app.route('/api/data')
def get_data():
    api_key = request.headers.get('X-API-Key')
    if not api_key:
        raise Unauthorized("Missing API key")

    user = db.validate_api_key(api_key)
    if not user:
        raise Unauthorized("Invalid API key")

    return {'data': fetch_user_data(user.id)}
```

### Bearer Token (JWT)
```python
# Client includes in Authorization header
curl -H "Authorization: Bearer eyJhbGc..." https://api.example.com/data

# Server validates
def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            raise Unauthorized("Missing or invalid Authorization header")

        token = auth_header[7:]  # Remove 'Bearer '
        try:
            payload = jwt.decode(token, os.environ['JWT_SECRET'], algorithms=['RS256'])
        except jwt.InvalidSignatureError:
            raise Unauthorized("Invalid token signature")
        except jwt.ExpiredSignatureError:
            raise Unauthorized("Token expired")

        g.user_id = payload['sub']
        return f(*args, **kwargs)
    return decorated

@app.route('/api/data')
@require_auth
def get_data():
    return {'data': fetch_user_data(g.user_id)}
```

## Input Validation

### Schema Validation
```python
from pydantic import BaseModel, Field, validator

class CreateUserRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    name: str = Field(..., min_length=1, max_length=255)
    age: int = Field(ge=18, le=120)  # Greater/equal 18, less/equal 120

    @validator('email')
    def email_must_be_valid(cls, v):
        if '@' not in v:
            raise ValueError('Invalid email format')
        return v.lower()

    @validator('password')
    def password_must_be_strong(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain uppercase')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain digit')
        return v

# FastAPI
from fastapi import FastAPI, HTTPException

app = FastAPI()

@app.post('/users')
async def create_user(user: CreateUserRequest):
    # Pydantic validates automatically
    # Invalid request returns 422 Unprocessable Entity
    db.create_user(user.email, user.password, user.name)
    return {'status': 'created'}
```

### Type Coercion Protection
```python
# VULNERABLE - Type confusion
user_id = request.args.get('id')  # Always a string
user = db.query("SELECT * FROM users WHERE id = ?", (user_id,))
# If db converts '1' == 1, attacker might exploit

# SAFE - Explicit type validation
try:
    user_id = int(request.args.get('id'))
except (ValueError, TypeError):
    raise BadRequest("Invalid user ID")

if user_id < 0:
    raise BadRequest("User ID must be positive")

user = db.query("SELECT * FROM users WHERE id = ?", (user_id,))
```

## Rate Limiting

### Per-Endpoint Rate Limits
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(app=app, key_func=get_remote_address)

@app.route('/api/login', methods=['POST'])
@limiter.limit("5 per minute")  # 5 attempts per minute per IP
def login():
    # Rate limit enforced
    pass

@app.route('/api/search')
@limiter.limit("100 per hour")  # 100 searches per hour per user
def search():
    pass
```

### Redis-Based Rate Limiting
```python
import redis
from datetime import datetime, timedelta

class RateLimiter:
    def __init__(self, redis_client):
        self.redis = redis_client

    def is_allowed(self, key, limit, window_seconds):
        # key = user_id or IP
        # limit = max requests
        # window_seconds = time window

        current = datetime.now().timestamp()
        window_start = current - window_seconds

        # Remove old requests outside window
        self.redis.zremrangebyscore(key, 0, window_start)

        # Count requests in window
        count = self.redis.zcard(key)

        if count >= limit:
            return False

        # Add current request
        self.redis.zadd(key, {str(current): current})
        self.redis.expire(key, window_seconds)

        return True

limiter = RateLimiter(redis.Redis())

@app.route('/api/expensive-operation')
@require_auth
def expensive_operation():
    if not limiter.is_allowed(f'user:{g.user_id}', limit=10, window_seconds=3600):
        raise TooManyRequests("Rate limit exceeded")

    # Process request
    return {'result': process_data()}
```

## HTTP Security Headers

```python
# Add security headers to all responses
@app.after_request
def add_security_headers(response):
    # Prevent MIME sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'

    # Clickjacking protection
    response.headers['X-Frame-Options'] = 'DENY'

    # XSS protection (legacy)
    response.headers['X-XSS-Protection'] = '1; mode=block'

    # HSTS (HTTPS only)
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

    # CSP
    response.headers['Content-Security-Policy'] = "default-src 'self'"

    # Referrer policy
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

    # Permissions policy
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'

    return response
```

## CORS Configuration

### Secure CORS
```python
from flask_cors import CORS

# VULNERABLE - Allow all origins
CORS(app)

# SAFE - Specific origins
CORS(app, resources={
    r"/api/*": {
        "origins": ["https://app.example.com", "https://www.example.com"],
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization"],
        "expose_headers": ["X-Total-Count"],
        "supports_credentials": True,
        "max_age": 86400
    }
})

# SAFE - Dynamic origin validation
def is_valid_origin(origin):
    valid_origins = ["https://app.example.com", "https://www.example.com"]
    return origin in valid_origins

@app.before_request
def check_cors():
    origin = request.headers.get('Origin')
    if origin and not is_valid_origin(origin):
        raise Forbidden("Invalid origin")
```

## Error Handling

### Safe Error Messages
```python
# VULNERABLE - Expose internals
@app.errorhandler(Exception)
def handle_error(e):
    return {'error': str(e)}, 500  # Shows stack trace, SQL, etc.

# SAFE - Generic messages to client, detailed logs on server
@app.errorhandler(Exception)
def handle_error(e):
    logger.error(f"Unexpected error: {type(e).__name__}: {str(e)}")

    if isinstance(e, BadRequest):
        return {'error': str(e)}, 400
    elif isinstance(e, Unauthorized):
        return {'error': 'Unauthorized'}, 401
    elif isinstance(e, Forbidden):
        return {'error': 'Forbidden'}, 403
    else:
        # Generic error to client
        return {'error': 'Internal server error'}, 500

    return response
```

## API Versioning & Deprecation

```python
# Version in URL
@app.route('/api/v1/users')
def list_users_v1():
    pass

@app.route('/api/v2/users')
def list_users_v2():
    pass

# With deprecation warning
@app.route('/api/v1/users')
def list_users_v1():
    response = make_response(fetch_users())
    response.headers['Deprecation'] = 'true'
    response.headers['Sunset'] = 'Sat, 01 Jan 2025 00:00:00 GMT'
    response.headers['Link'] = '</api/v2/users>; rel="successor-version"'
    return response
```

## Deployment Checklist

- [ ] All API endpoints require authentication
- [ ] Authorization checked for each resource
- [ ] Input validation with schema validation library
- [ ] Rate limiting enforced on sensitive endpoints
- [ ] CORS configured with specific origins
- [ ] Security headers set on all responses
- [ ] HTTPS enforced (no HTTP)
- [ ] Error messages don't expose internals
- [ ] API keys stored as hashes (not plain text)
- [ ] JWT tokens expire within reasonable timeframe
- [ ] API versioning documented
- [ ] Deprecation path planned for old versions
- [ ] API documentation updated with security requirements
- [ ] Automated security testing in CI/CD

## References

- OWASP API Security Top 10: https://owasp.org/www-project-api-security/
- REST Security Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/REST_Security_Cheat_Sheet.html
