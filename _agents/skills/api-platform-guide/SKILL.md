---
skill_name: API Platform Guide
description: Build API catalogs, gateways, and developer portals with analytics
category: Platform Engineering
version: 1.0.0
---

# API Platform Guide

## Overview
API platforms unify service communication. Master gateways, catalogs, and developer experience.

## API Catalog

### OpenAPI Registry

```yaml
openapi: 3.0.0
info:
  title: User API
  version: 1.0.0
  x-internal: false
  x-team: user-team
  x-severity: critical

paths:
  /users:
    get:
      x-rate-limit: 1000/hour
      x-authentication: required
      responses:
        200:
          description: Users list
```

### Discoverability

- Search by endpoint, tag, team
- Usage statistics per API
- Breaking change alerts
- Deprecation warnings

## API Gateway

### Request Flow

```
Client → Gateway → Service
         ├─ Authentication
         ├─ Rate limiting
         ├─ Request validation
         ├─ Routing
         └─ Response transformation
```

### Configuration

```yaml
routes:
  - path: /users/*
    target: user-service
    rateLimit: 1000/hour
    auth: required
    timeout: 30s
    retries: 3
```

## Developer Portal

### Self-Service Features

- API discovery and search
- Interactive API documentation
- API key management
- Usage analytics
- Quota management

## Production Checklist

- [ ] Register all APIs in catalog
- [ ] Implement API gateway
- [ ] Create developer portal
- [ ] Document API contracts
- [ ] Set rate limits
- [ ] Monitor API usage
- [ ] Plan versioning strategy
- [ ] Establish SLAs
- [ ] Create incident runbooks
- [ ] Build developer community
