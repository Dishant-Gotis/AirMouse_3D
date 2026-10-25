---
skill_name: api-gateway-patterns
description: API gateway patterns including authentication, routing, rate limiting, circuit breaking, aggregation
category: Backend Development
version: 1.0.0
---

# API Gateway Patterns

## Authentication and Authorization

```python
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer

app = FastAPI()
security = HTTPBearer()

class APIGateway:
  def __init__(self):
    self.services = {
      "users": "http://users-service:8001",
      "orders": "http://orders-service:8002",
      "payments": "http://payments-service:8003"
    }

  async def authenticate(self, credentials):
    """Authenticate incoming request"""
    token = credentials.credentials

    try:
      payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
      user_id = payload.get("sub")

      if not user_id:
        raise HTTPException(status_code=401)

      return user_id
    except jwt.InvalidTokenError:
      raise HTTPException(status_code=401)

  async def authorize(self, user_id: str, service: str, action: str):
    """Check authorization for service"""
    permissions = await self.get_user_permissions(user_id)

    if not self.has_permission(permissions, service, action):
      raise HTTPException(status_code=403)

    return True

  async def get_user_permissions(self, user_id: str) -> dict:
    """Fetch user permissions"""
    async with aiohttp.ClientSession() as session:
      async with session.get(f"{self.services['users']}/permissions/{user_id}") as resp:
        return await resp.json()

  def has_permission(self, permissions: dict, service: str, action: str) -> bool:
    """Check if user has permission"""
    return f"{service}:{action}" in permissions.get("scopes", [])

gateway = APIGateway()

@app.get("/api/users/{user_id}")
async def get_user(user_id: str, credentials = Depends(security)):
  user_id = await gateway.authenticate(credentials)
  await gateway.authorize(user_id, "users", "read")

  async with aiohttp.ClientSession() as session:
    async with session.get(f"{gateway.services['users']}/{user_id}") as resp:
      return await resp.json()
```

## Request Routing

```python
class Router:
  def __init__(self):
    self.routes = {
      "/api/users": "users-service",
      "/api/orders": "orders-service",
      "/api/payments": "payments-service",
      "/api/inventory": "inventory-service"
    }

  def get_service(self, path: str) -> str:
    """Route request to service"""
    for route_prefix, service in self.routes.items():
      if path.startswith(route_prefix):
        return service

    raise ValueError(f"No service for path: {path}")

  async def forward(self, service: str, method: str, path: str, headers: dict, body: dict = None):
    """Forward request to service"""
    service_url = os.getenv(f"{service.upper()}_URL")
    url = f"{service_url}{path}"

    async with aiohttp.ClientSession() as session:
      async with session.request(method, url, headers=headers, json=body) as resp:
        return resp.status, await resp.json()

router = Router()

@app.api_route("/api/{service_path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def gateway_route(request: Request, service_path: str):
  path = f"/api/{service_path}"
  service = router.get_service(path)

  body = await request.json() if request.method in ["POST", "PUT"] else None

  status, data = await router.forward(
    service,
    request.method,
    path,
    dict(request.headers),
    body
  )

  return JSONResponse(status_code=status, content=data)
```

## Rate Limiting at Gateway

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

class RateLimitingGateway:
  def __init__(self, redis_client):
    self.redis = redis_client

  async def get_rate_limit(self, user_id: str) -> dict:
    """Get rate limit for user"""
    plan = await self.get_user_plan(user_id)

    limits = {
      "free": {"requests": 100, "window": 3600},
      "pro": {"requests": 10000, "window": 3600},
      "enterprise": {"requests": None, "window": None}
    }

    return limits.get(plan, limits["free"])

  async def check_rate_limit(self, user_id: str) -> bool:
    """Check if request is within rate limit"""
    limit = await self.get_rate_limit(user_id)

    if limit["requests"] is None:  # Unlimited
      return True

    key = f"rate:{user_id}"
    current = await self.redis.incr(key)

    if current == 1:
      await self.redis.expire(key, limit["window"])

    return current <= limit["requests"]

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
  user_id = request.state.user_id
  gateway = RateLimitingGateway(redis_client)

  if not await gateway.check_rate_limit(user_id):
    return JSONResponse(
      status_code=429,
      content={"error": "Rate limit exceeded"}
    )

  return await call_next(request)
```

## Service Aggregation

```python
class ServiceAggregator:
  def __init__(self, services: dict):
    self.services = services

  async def aggregate(self, user_id: str) -> dict:
    """Aggregate data from multiple services"""
    async with aiohttp.ClientSession() as session:
      tasks = [
        self.fetch_user(session, user_id),
        self.fetch_orders(session, user_id),
        self.fetch_recommendations(session, user_id)
      ]

      user, orders, recommendations = await asyncio.gather(*tasks)

      return {
        "user": user,
        "orders": orders,
        "recommendations": recommendations
      }

  async def fetch_user(self, session, user_id: str):
    async with session.get(f"{self.services['users']}/users/{user_id}") as resp:
      return await resp.json()

  async def fetch_orders(self, session, user_id: str):
    async with session.get(f"{self.services['orders']}/users/{user_id}/orders") as resp:
      return await resp.json()

  async def fetch_recommendations(self, session, user_id: str):
    async with session.get(f"{self.services['recommendations']}/recommendations/{user_id}") as resp:
      return await resp.json()

@app.get("/api/dashboard")
async def get_dashboard(user_id: str = Depends(get_current_user)):
  aggregator = ServiceAggregator({
    "users": "http://users-service:8001",
    "orders": "http://orders-service:8002",
    "recommendations": "http://recommendations-service:8003"
  })

  return await aggregator.aggregate(user_id)
```

## Protocol Translation

```python
class ProtocolTranslator:
  async def translate_rest_to_grpc(self, rest_request: dict, grpc_stub):
    """Convert REST to gRPC"""
    grpc_request = self.build_grpc_request(rest_request)
    response = await grpc_stub.CallRPC(grpc_request)
    return self.grpc_response_to_rest(response)

  async def translate_rest_to_graphql(self, rest_request: dict, graphql_endpoint: str):
    """Convert REST to GraphQL"""
    graphql_query = self.build_graphql_query(rest_request)

    async with aiohttp.ClientSession() as session:
      async with session.post(graphql_endpoint, json={"query": graphql_query}) as resp:
        return await resp.json()

# gRPC service through gateway
@app.get("/api/grpc/users/{user_id}")
async def grpc_gateway(user_id: str):
  channel = grpc.aio.secure_channel('grpc-service:50051', grpc.ssl_channel_credentials())
  stub = UserServiceStub(channel)

  request = GetUserRequest(user_id=user_id)
  response = await stub.GetUser(request)

  return MessageToDict(response)

# GraphQL through gateway
@app.post("/api/graphql")
async def graphql_gateway(query: dict):
  translator = ProtocolTranslator()

  result = await translator.translate_rest_to_graphql(
    query,
    "http://graphql-service:8001/graphql"
  )

  return result
```

## Logging and Monitoring

```python
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
  request_id = str(uuid.uuid4())
  request.state.request_id = request_id

  start_time = time.time()

  response = await call_next(request)

  process_time = time.time() - start_time

  logger.info(
    "API Gateway Request",
    extra={
      "request_id": request_id,
      "method": request.method,
      "path": request.url.path,
      "status": response.status_code,
      "process_time": process_time,
      "user_id": request.state.get("user_id")
    }
  )

  response.headers["X-Request-ID"] = request_id
  response.headers["X-Process-Time"] = str(process_time)

  return response
```

