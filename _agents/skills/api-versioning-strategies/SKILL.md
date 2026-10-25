---
skill_name: api-versioning-strategies
description: API versioning strategies including URL, header, query param approaches, deprecation, changelog
category: Backend Development
version: 1.0.0
---

# API Versioning Strategies

## URL-Based Versioning

```python
from fastapi import FastAPI, APIRouter

app = FastAPI()

# Version 1
v1_router = APIRouter(prefix="/api/v1")

@v1_router.get("/users/{user_id}")
async def get_user_v1(user_id: int):
  """Version 1: Returns basic user info"""
  return {
    "id": user_id,
    "email": "user@example.com",
    "name": "John Doe"
  }

# Version 2
v2_router = APIRouter(prefix="/api/v2")

@v2_router.get("/users/{user_id}")
async def get_user_v2(user_id: int):
  """Version 2: Returns extended user info"""
  return {
    "id": user_id,
    "email": "user@example.com",
    "name": "John Doe",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-15T00:00:00Z",
    "phone": "+1234567890",
    "avatar_url": "https://example.com/avatar.jpg"
  }

app.include_router(v1_router)
app.include_router(v2_router)

# Deprecation warning
@v1_router.get("/deprecated-endpoint")
async def deprecated():
  from fastapi.responses import JSONResponse
  return JSONResponse(
    status_code=200,
    content={"data": "value"},
    headers={"Deprecation": "true", "Sunset": "Sun, 01 Jan 2025 00:00:00 GMT"}
  )
```

## Header-Based Versioning

```python
from fastapi import Header, HTTPException

@app.get("/users/{user_id}")
async def get_user(user_id: int, accept_version: str = Header(None)):
  """Version negotiation via Accept-Version header"""
  if not accept_version or accept_version == "v1":
    return {
      "id": user_id,
      "name": "John Doe"
    }
  elif accept_version == "v2":
    return {
      "id": user_id,
      "name": "John Doe",
      "created_at": "2024-01-01T00:00:00Z"
    }
  else:
    raise HTTPException(status_code=406, detail="Unsupported version")

# Client usage:
# GET /users/123
# Accept-Version: v2
```

## Content-Type Versioning

```python
@app.get("/users/{user_id}")
async def get_user(user_id: int, accept: str = Header("application/json")):
  """Version negotiation via Accept header"""
  if "application/vnd.api.v2+json" in accept:
    # Version 2 response
    return {
      "data": {
        "id": user_id,
        "name": "John Doe",
        "created_at": "2024-01-01"
      }
    }
  else:
    # Default version 1
    return {
      "id": user_id,
      "name": "John Doe"
    }

# Client usage:
# GET /users/123
# Accept: application/vnd.api.v2+json
```

## Query Parameter Versioning

```python
from typing import Optional

@app.get("/users/{user_id}")
async def get_user(user_id: int, api_version: Optional[str] = None):
  """Version negotiation via query parameter"""
  version = api_version or "v1"

  user = {"id": user_id, "name": "John Doe"}

  if version == "v2":
    user["created_at"] = "2024-01-01"
    user["email"] = "user@example.com"

  if version == "v3":
    user.update({
      "created_at": "2024-01-01",
      "email": "user@example.com",
      "phone": "+1234567890",
      "updated_at": "2024-01-15"
    })

  return user

# Usage:
# GET /users/123?api_version=v2
```

## Deprecation Headers

```python
from datetime import datetime, timedelta

def add_deprecation_headers(response, sunset_date: datetime = None):
  """Add standard deprecation headers"""
  response.headers["Deprecation"] = "true"

  if sunset_date:
    response.headers["Sunset"] = sunset_date.strftime("%a, %d %b %Y %H:%M:%S GMT")

  response.headers["Link"] = '</api/v2/users>; rel="successor-version"'

  return response

@app.get("/users/{user_id}")
async def get_user_v1(user_id: int):
  from fastapi.responses import JSONResponse

  response = JSONResponse({"id": user_id, "name": "John"})

  sunset = datetime.utcnow() + timedelta(days=90)
  add_deprecation_headers(response, sunset)

  return response
```

## Changelog

```python
@app.get("/changelog")
async def get_changelog():
  """API changelog and version history"""
  return {
    "changelog": [
      {
        "version": "v3",
        "released": "2024-01-20",
        "status": "current",
        "changes": [
          "Added phone field to User",
          "Added updated_at timestamp",
          "Deprecated v1 API"
        ]
      },
      {
        "version": "v2",
        "released": "2024-01-10",
        "status": "deprecated",
        "sunset": "2025-01-01",
        "changes": [
          "Added email field",
          "Added created_at timestamp",
          "Improved performance"
        ]
      },
      {
        "version": "v1",
        "released": "2023-01-01",
        "status": "sunset",
        "sunset": "2024-01-01",
        "changes": [
          "Initial version"
        ]
      }
    ]
  }

@app.get("/migrations")
async def get_migration_guides():
  """Migration guides between versions"""
  return {
    "v1_to_v2": {
      "breaking_changes": [],
      "new_fields": ["email", "created_at"],
      "example": {
        "v1_request": "GET /api/v1/users/123",
        "v2_request": "GET /api/v2/users/123",
        "v2_response": {
          "id": 123,
          "email": "user@example.com",
          "created_at": "2024-01-01T00:00:00Z"
        }
      }
    },
    "v2_to_v3": {
      "breaking_changes": [],
      "new_fields": ["phone", "updated_at"],
      "deprecated_fields": []
    }
  }
```

## Version Support Matrix

```python
@app.get("/api/versions")
async def supported_versions():
  """List supported API versions"""
  return {
    "supported_versions": [
      {
        "version": "v3",
        "status": "current",
        "release_date": "2024-01-20",
        "support_until": None,
        "endpoints": ["GET /users", "POST /users", "PUT /users/{id}"]
      },
      {
        "version": "v2",
        "status": "deprecated",
        "release_date": "2024-01-10",
        "support_until": "2025-01-01",
        "migration_guide": "https://docs.example.com/migrate-v2-to-v3"
      },
      {
        "version": "v1",
        "status": "sunset",
        "release_date": "2023-01-01",
        "support_until": "2024-01-01"
      }
    ]
  }
```

