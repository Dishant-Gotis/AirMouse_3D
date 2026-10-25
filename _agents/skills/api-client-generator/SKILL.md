---
skill_name: api-client-generator
description: Auto-generate type-safe API clients from OpenAPI specs with error handling, retries, and caching
category: Developer Tools
version: 1.0.0
---

# API Client Generator: From Spec to Production Code

Automatically generate type-safe API clients from OpenAPI/Swagger specifications. Eliminates manual boilerplate and ensures consistency with backend API.

## Part 1: OpenAPI Specification Basics

### What is OpenAPI?

```
OpenAPI (formerly Swagger) = Standard specification for REST APIs

DESCRIBES:
- Endpoints (routes)
- Methods (GET, POST, etc.)
- Parameters (query, path, body)
- Responses (status, data structure)
- Auth (how to authenticate)

EXAMPLE SPEC (YAML):
openapi: 3.0.0
info:
  title: User API
  version: 1.0.0

paths:
  /users:
    get:
      summary: List all users
      parameters:
        - name: limit
          in: query
          schema:
            type: integer
      responses:
        '200':
          description: List of users
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/User'

    post:
      summary: Create a user
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UserInput'
      responses:
        '201':
          description: User created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'

  /users/{id}:
    get:
      summary: Get user by ID
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: User found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'
        '404':
          description: User not found

components:
  schemas:
    User:
      type: object
      properties:
        id:
          type: string
        name:
          type: string
        email:
          type: string
      required:
        - id
        - name
        - email

    UserInput:
      type: object
      properties:
        name:
          type: string
        email:
          type: string
      required:
        - name
        - email
```
```

## Part 2: Code Generation Tools

### OpenAPI Generator

```
Open source, supports 50+ languages

Installation:
npm install -g @openapitools/openapi-generator-cli

Command:
openapi-generator-cli generate \
  -i api.yaml \
  -g typescript-axios \
  -o ./generated

GENERATES:
- models.ts (type definitions for request/response)
- api.ts (client class with methods)
- index.ts (exports)

EXAMPLE GENERATED CODE:
```typescript
// models.ts
export interface User {
  id: string;
  name: string;
  email: string;
}

export interface UserInput {
  name: string;
  email: string;
}

// api.ts
export class UserApi {
  constructor(private basePath: string, private axios: AxiosInstance) {}

  async listUsers(limit?: number) {
    return this.axios.get<User[]>('/users', {
      params: { limit }
    });
  }

  async createUser(body: UserInput) {
    return this.axios.post<User>('/users', body);
  }

  async getUser(id: string) {
    return this.axios.get<User>(`/users/${id}`);
  }
}
```

USAGE:
```typescript
import { UserApi } from './generated';
import axios from 'axios';

const api = new UserApi('https://api.example.com', axios);

const users = await api.listUsers(10);
const newUser = await api.createUser({ name: 'John', email: 'john@example.com' });
const user = await api.getUser('123');
```
```

### Manual Option: Swagger Codegen

```
Java-based, more configurable

npm install -g swagger-codegen

swagger-codegen generate \
  -i api.yaml \
  -l typescript-fetch \
  -o ./generated

ADVANTAGE: Wider customization options
DISADVANTAGE: Slower, requires Java
```

## Part 3: Error Handling

### Generated Error Handling

```
ADD ERROR HANDLING to generated client:

// client.ts
import { UserApi } from './generated';
import axios from 'axios';

const axiosInstance = axios.create({
  baseURL: 'https://api.example.com',
  timeout: 5000
});

// Error interceptor
axiosInstance.interceptors.response.use(
  response => response,
  error => {
    if (error.response) {
      // Server error (400, 500, etc)
      const status = error.response.status;
      const message = error.response.data?.message || 'Unknown error';

      if (status === 404) {
        throw new NotFoundError(message);
      } else if (status === 401) {
        throw new UnauthorizedError(message);
      } else if (status === 400) {
        throw new BadRequestError(message);
      } else if (status === 500) {
        throw new InternalServerError(message);
      } else {
        throw new ApiError(status, message);
      }
    } else if (error.request) {
      // Request made but no response (network error)
      throw new NetworkError('No response from server');
    } else {
      // Other errors
      throw error;
    }
  }
);

export const userApi = new UserApi('', axiosInstance);

// Custom error classes
export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

export class NotFoundError extends ApiError {
  constructor(message: string) {
    super(404, message);
    this.name = 'NotFoundError';
  }
}
```

USAGE:
```typescript
try {
  const user = await userApi.getUser('999');
} catch (error) {
  if (error instanceof NotFoundError) {
    console.log('User not found');
  } else if (error instanceof UnauthorizedError) {
    console.log('Please login');
    redirectToLogin();
  } else if (error instanceof NetworkError) {
    console.log('Check your internet connection');
  } else {
    console.error('Unexpected error:', error);
  }
}
```
```

## Part 4: Retry Logic

### Exponential Backoff

```
PROBLEM: Temporary failures (network blip, service restarting)
SOLUTION: Automatically retry with exponential backoff

Algorithm:
```
Attempt 1: Fails immediately
Attempt 2: Wait 100ms, retry
Attempt 3: Wait 200ms, retry
Attempt 4: Wait 400ms, retry
Attempt 5: Wait 800ms, fail with error
```

IMPLEMENTATION:
```typescript
async function retryWithBackoff<T>(
  fn: () => Promise<T>,
  maxRetries: number = 3
): Promise<T> {
  let lastError: Error;

  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;

      // Don't retry on client errors (4xx)
      if (error.status && error.status < 500) {
        throw error;
      }

      // Wait before retrying
      const waitMs = Math.pow(2, attempt) * 100;
      await new Promise(resolve => setTimeout(resolve, waitMs));
    }
  }

  throw lastError;
}

// USE:
const user = await retryWithBackoff(() => userApi.getUser('123'));
```

CONFIGURE IN INTERCEPTOR:
```typescript
axiosInstance.interceptors.response.use(
  response => response,
  async error => {
    const config = error.config;

    if (!config || !config.retry) {
      config.retry = 0;
    }

    config.retry += 1;

    if (config.retry <= 3 && error.response?.status >= 500) {
      // Server error, retry
      const delay = Math.pow(2, config.retry - 1) * 100;
      await new Promise(resolve => setTimeout(resolve, delay));
      return axiosInstance(config);
    }

    return Promise.reject(error);
  }
);
```
```

## Part 5: Caching Strategy

### Simple Response Caching

```
Cache GET requests (safe to cache)
Invalidate on mutation (POST, PUT, DELETE)

IMPLEMENTATION:
```typescript
const cache = new Map<string, CacheEntry>();

interface CacheEntry {
  data: any;
  timestamp: number;
  ttl: number; // Time to live in ms
}

// Cache interceptor
axiosInstance.interceptors.request.use(
  config => {
    if (config.method === 'get') {
      const cached = cache.get(config.url);
      if (cached && Date.now() - cached.timestamp < cached.ttl) {
        return Promise.reject({ cached: cached.data });
      }
    }
    return config;
  }
);

axiosInstance.interceptors.response.use(
  response => {
    if (response.config.method === 'get') {
      cache.set(response.config.url, {
        data: response.data,
        timestamp: Date.now(),
        ttl: 5 * 60 * 1000 // 5 minutes
      });
    }
    return response;
  },
  error => {
    if (error.cached) {
      return Promise.resolve({ data: error.cached });
    }
    return Promise.reject(error);
  }
);

// Invalidate on mutation
axiosInstance.interceptors.request.use(
  config => {
    if (['post', 'put', 'delete'].includes(config.method)) {
      // Clear all cached GETs for this resource
      const resource = config.url.split('/')[1]; // /users → users
      const keysToDelete = Array.from(cache.keys())
        .filter(key => key.includes(`/${resource}`));
      keysToDelete.forEach(key => cache.delete(key));
    }
    return config;
  }
);
```

USAGE:
```typescript
// First call: hits API
const users1 = await userApi.listUsers();

// Second call (within 5 min): returns cached result
const users2 = await userApi.listUsers(); // instant, cached

// Create user: invalidates users list cache
await userApi.createUser({ name: 'Jane' });

// Next call: cache cleared, hits API again
const users3 = await userApi.listUsers();
```
```

## Part 6: Production Setup

### Full-Featured Client

```
Combine everything: Error handling + Retries + Caching

// api-client.ts
import axios, { AxiosInstance } from 'axios';
import { UserApi } from './generated';

export class ApiClient {
  private axios: AxiosInstance;
  public users: UserApi;

  constructor(baseURL: string, authToken?: string) {
    this.axios = axios.create({
      baseURL,
      timeout: 5000,
      headers: authToken ? { Authorization: `Bearer ${authToken}` } : {}
    });

    this.setupInterceptors();
    this.users = new UserApi('', this.axios);
  }

  private setupInterceptors() {
    // Error handling
    this.axios.interceptors.response.use(
      response => response,
      error => this.handleError(error)
    );

    // Retry logic
    this.axios.interceptors.response.use(
      response => response,
      error => this.retryIfNeeded(error)
    );

    // Caching
    this.setupCaching();
  }

  private handleError(error: any) {
    if (error.response?.status === 401) {
      // Refresh token or redirect to login
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }

  private async retryIfNeeded(error: any) {
    // ... retry logic
  }

  private setupCaching() {
    // ... caching logic
  }
}

// usage.ts
import { ApiClient } from './api-client';

const apiClient = new ApiClient(
  'https://api.example.com',
  localStorage.getItem('authToken')
);

// Now all requests have error handling, retries, and caching
const users = await apiClient.users.listUsers();
```

### Integration with Frontend

```
React example:

// hooks/useUsers.ts
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../api-client';

export function useUsers() {
  return useQuery({
    queryKey: ['users'],
    queryFn: () => apiClient.users.listUsers()
  });
}

// Components/UserList.tsx
import { useUsers } from '../hooks/useUsers';

export function UserList() {
  const { data: users, isLoading, error } = useUsers();

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <ul>
      {users?.map(user => (
        <li key={user.id}>{user.name}</li>
      ))}
    </ul>
  );
}
```

This gives you:
- Type safety (TypeScript)
- Automatic caching (React Query)
- Error handling
- Retry logic
- Request deduplication
All with generated code!
```

## Summary

Generate API clients with:

1. **OpenAPI spec** (document your API)
2. **Code generation** (OpenAPI Generator or similar)
3. **Error handling** (custom error classes)
4. **Retry logic** (exponential backoff)
5. **Caching** (reduce API calls)
6. **Integration** (React Query, Vue use, etc.)

Result: Type-safe, reliable, cacheable API client that stays in sync with backend.

Every time backend API changes, regenerate client - always in sync, zero manual updates.
