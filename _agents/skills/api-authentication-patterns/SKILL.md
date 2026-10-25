---
skill_name: API Authentication & Token Patterns
description: Implement API keys, OAuth 2.0, mTLS, token rotation, rate limiting, and signature verification
category: Advanced Security
version: 1.0.0
---

# API Authentication & Token Patterns

## Overview
Secure APIs require authentication, authorization, rate limiting, and token management. Master modern auth patterns.

## API Key Authentication

### Basic API Keys

```python
class APIKeyAuth:
    def __init__(self):
        self.keys = {}

    def api_key_pattern(self):
        """Simple but limited"""
        return {
            'approach': 'Client sends X-API-Key header with secret',
            'example': {
                'request': 'GET /api/users',
                'header': 'X-API-Key: sk_live_abcd1234efgh5678'
            },
            'generation': 'Generate random 32+ byte key, store hash',
            'storage': 'Never log in logs, use secret manager',
            'limitations': [
                'No scope/permissions',
                'No expiry',
                'Lost key = full access'
            ]
        }

    def api_key_best_practices(self):
        """How to do it right"""
        return {
            'prefix': 'Include prefix for identification (sk_live_)',
            'checksum': 'Include checksum to validate format early',
            'scopes': 'Limit key to specific endpoints/permissions',
            'rotation': 'Rotate every 90 days',
            'monitoring': 'Alert on unusual usage patterns'
        }

# Usage
api_key = APIKeyAuth()
pattern = api_key.api_key_pattern()
print(f"Limitation: {pattern['limitations']}")
```

## OAuth 2.0

### OAuth 2.0 Flows

```python
class OAuth2:
    def __init__(self):
        self.flows = []

    def authorization_code_flow(self):
        """For web apps and mobile apps"""
        return {
            'scenario': 'User logs in with Google/GitHub',
            'flow': [
                '1. User visits example.com',
                '2. example.com redirects to accounts.google.com',
                '3. User logs in to Google, grants permission',
                '4. Google redirects back to example.com with code',
                '5. example.com backend exchanges code for token',
                '6. example.com now has access token to call Google API'
            ],
            'benefit': 'User password never shared with example.com',
            'use_case': 'Third-party login, delegated access'
        }

    def client_credentials_flow(self):
        """For service-to-service"""
        return {
            'scenario': 'Payment API calls Notification API',
            'flow': [
                '1. Payment API requests token from Auth Server',
                '2. Sends client_id and client_secret',
                '3. Auth Server returns access token',
                '4. Payment API calls Notification API with token',
                '5. Notification API validates token, allows request'
            ],
            'security': 'Both credentials required, no user context'
        }

    def token_endpoint(self):
        """Request access token"""
        code = '''
POST /oauth/token

# Authorization Code Flow
grant_type=authorization_code&
code=ABCD1234&
client_id=my-app-123&
client_secret=super-secret&
redirect_uri=https://example.com/callback

# Response
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "refresh-token-abc123"
}
'''
        return code

# Usage
oauth = OAuth2()
auth_code = oauth.authorization_code_flow()
print(f"User password: {auth_code['benefit']}")
```

## Mutual TLS (mTLS)

### Certificate-Based Authentication

```python
class MutualTLS:
    def __init__(self):
        self.setup = {}

    def mtls_overview(self):
        """Both client and server authenticate"""
        return {
            'concept': 'TLS but both sides present certificates',
            'server_cert': 'Server presents certificate (normal HTTPS)',
            'client_cert': 'Client also presents certificate',
            'mutual_verification': 'Both verify each other"s certificates',
            'use_case': 'Service-to-service communication'
        }

    def mtls_setup(self):
        """How to implement"""
        return {
            'step_1_ca': 'Create Certificate Authority (CA)',
            'step_2_server_cert': 'Generate server certificate signed by CA',
            'step_3_client_cert': 'Generate client certificate signed by CA',
            'step_4_distribute': 'Give client cert to service, server cert to API',
            'step_5_verify': 'Both sides verify certificate chain'
        }

    def nginx_mTLS_config(self):
        """Nginx example"""
        code = '''
server {
    listen 8443 ssl;
    server_name api.example.com;

    # Server certificate
    ssl_certificate /etc/nginx/certs/server.crt;
    ssl_certificate_key /etc/nginx/certs/server.key;

    # Client certificate verification
    ssl_client_certificate /etc/nginx/certs/ca.crt;
    ssl_verify_client on;
    ssl_verify_depth 2;

    # Accept only verified clients
    location / {
        proxy_pass http://backend;
    }
}
'''
        return code

# Usage
mtls = MutualTLS()
overview = mtls.mtls_overview()
print(f"mTLS concept: {overview['concept']}")
```

## Token Management

### JWT (JSON Web Tokens)

```python
class JWT:
    def __init__(self):
        self.tokens = []

    def jwt_structure(self):
        """Header.Payload.Signature"""
        return {
            'format': 'eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1c2VyLTEyMyJ9.abc123',
            'header': {
                'alg': 'HS256 or RS256 (signing algorithm)',
                'typ': 'JWT'
            },
            'payload': {
                'sub': 'user-123 (subject)',
                'aud': 'api.example.com (audience)',
                'iat': 1615862400,  # Issued at
                'exp': 1615866000,  # Expires at (15 min later)',
                'scopes': ['read:users', 'write:posts']
            },
            'signature': 'HMACSHA256(header.payload, secret)'
        }

    def jwt_validation(self):
        """Verify JWT before accepting"""
        return {
            'check_signature': 'Verify signature matches',
            'check_exp': 'Verify exp > now (not expired)',
            'check_iat': 'Verify iat is in past',
            'check_aud': 'Verify audience matches service',
            'check_nbf': 'Verify not before time'
        }

    def token_rotation(self):
        """Manage token lifecycle"""
        return {
            'short_lived_token': {
                'access_token': 'Expires in 15-60 minutes',
                'benefit': 'If compromised, limited exposure'
            },
            'long_lived_refresh': {
                'refresh_token': 'Expires in days/weeks',
                'use': 'Get new access token without re-auth',
                'secure_storage': 'Only in httpOnly cookie'
            },
            'token_expiry': 'Force logout periodically'
        }

# Usage
jwt = JWT()
structure = jwt.jwt_structure()
print(f"JWT exp claim: {structure['payload']['exp']}")
```

## Rate Limiting

### Rate Limit Strategy

```python
class RateLimiting:
    def __init__(self):
        self.policies = []

    def rate_limit_levels(self):
        """Different limits per key/user"""
        return {
            'public': {
                'requests_per_minute': 10,
                'requests_per_hour': 100
            },
            'authenticated': {
                'requests_per_minute': 100,
                'requests_per_hour': 10000
            },
            'premium': {
                'requests_per_minute': 1000,
                'requests_per_hour': 100000
            },
            'admin': {
                'requests_per_minute': 'Unlimited',
                'requests_per_hour': 'Unlimited'
            }
        }

    def rate_limit_headers(self):
        """Inform clients of limits"""
        return {
            'X-RateLimit-Limit': 100,
            'X-RateLimit-Remaining': 95,
            'X-RateLimit-Reset': 1615862460,
            '429_Too_Many_Requests': 'Returned when limit exceeded'
        }

    def enforcement_strategies(self):
        """How to implement"""
        return {
            'per_api_key': 'Track requests per key',
            'per_ip': 'Track by source IP (fallback)',
            'per_user': 'Track by authenticated user ID',
            'distributed': 'Use Redis for multi-server setups'
        }

# Usage
rate_limit = RateLimiting()
levels = rate_limit.rate_limit_levels()
print(f"Premium limit: {levels['premium']}")
```

## Production Checklist

- [ ] Implement API authentication (OAuth, mTLS, or API keys)
- [ ] Use HTTPS for all API traffic
- [ ] Validate access tokens on every request
- [ ] Implement token expiry (short-lived tokens)
- [ ] Use refresh tokens for long-lived sessions
- [ ] Enable rate limiting with appropriate thresholds
- [ ] Return rate limit headers to clients
- [ ] Log all authentication failures
- [ ] Implement API versioning strategy
- [ ] Use API gateway for centralized auth/rate limiting
- [ ] Rotate secrets and certificates regularly
- [ ] Monitor for suspicious authentication patterns
