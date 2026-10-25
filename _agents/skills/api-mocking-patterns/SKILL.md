---
skill_name: api-mocking-patterns
description: API mocking - MSW, WireMock, Prism, contract-first development, testing strategies
category: [backend, advanced]
version: 1.0.0
---

# API Mocking Patterns

## Overview

Mock APIs enable frontend-backend parallel development, testing without live services, and contract-driven development.

## MSW (Mock Service Worker) - JavaScript

MSW intercepts network requests at the browser/Node.js level using service workers.

```javascript
// mocks/handlers.js
import { http, HttpResponse } from 'msw';

const API_BASE = 'https://api.example.com';

export const handlers = [
  // GET /users/:id
  http.get(`${API_BASE}/users/:id`, ({ params }) => {
    const { id } = params;

    return HttpResponse.json({
      id,
      name: `User ${id}`,
      email: `user${id}@example.com`,
      createdAt: new Date().toISOString()
    }, { status: 200 });
  }),

  // POST /users
  http.post(`${API_BASE}/users`, async ({ request }) => {
    const body = await request.json();

    if (!body.email || !body.name) {
      return HttpResponse.json(
        { error: 'Missing required fields' },
        { status: 400 }
      );
    }

    return HttpResponse.json(
      {
        id: Math.random().toString(36).substr(2, 9),
        ...body,
        createdAt: new Date().toISOString()
      },
      { status: 201 }
    );
  }),

  // DELETE /users/:id
  http.delete(`${API_BASE}/users/:id`, ({ params }) => {
    return new HttpResponse(null, { status: 204 });
  }),

  // Simulated network error
  http.get(`${API_BASE}/unstable`, () => {
    return HttpResponse.error();
  }),

  // Delayed response
  http.get(`${API_BASE}/slow`, async () => {
    await new Promise(resolve => setTimeout(resolve, 3000));

    return HttpResponse.json({ data: 'slow response' });
  })
];
```

**Browser setup**:

```javascript
// mocks/browser.js
import { setupWorker } from 'msw/browser';
import { handlers } from './handlers';

export const worker = setupWorker(...handlers);

// main.js or index.js
if (process.env.NODE_ENV === 'development') {
  import('./mocks/browser').then(({ worker }) => {
    worker.start();
  });
}
```

**Testing with MSW**:

```javascript
import { setupServer } from 'msw/node';
import { handlers } from './mocks/handlers';

const server = setupServer(...handlers);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('User API', () => {
  it('fetches user by ID', async () => {
    const response = await fetch('https://api.example.com/users/1');
    const user = await response.json();

    expect(user.id).toBe('1');
    expect(user.name).toBe('User 1');
  });

  it('handles validation errors', async () => {
    const response = await fetch('https://api.example.com/users', {
      method: 'POST',
      body: JSON.stringify({ name: 'John' }) // Missing email
    });

    expect(response.status).toBe(400);
    const error = await response.json();
    expect(error.error).toContain('required fields');
  });

  it('handles network errors', async () => {
    server.use(
      http.get('https://api.example.com/users/999', () => {
        return HttpResponse.error();
      })
    );

    await expect(fetch('https://api.example.com/users/999'))
      .rejects.toThrow();
  });

  it('simulates slow responses', async () => {
    server.use(
      http.get('https://api.example.com/users/slow', async () => {
        await new Promise(r => setTimeout(r, 100));
        return HttpResponse.json({ data: 'delayed' });
      })
    );

    const start = Date.now();
    await fetch('https://api.example.com/users/slow');
    const duration = Date.now() - start;

    expect(duration).toBeGreaterThan(100);
  });
});
```

## WireMock - JVM-Based

WireMock is Java-based, suitable for backend testing and standalone stub servers.

```java
import com.github.tomakehurst.wiremock.WireMockServer;
import static com.github.tomakehurst.wiremock.client.WireMock.*;
import static com.github.tomakehurst.wiremock.core.WireMockConfiguration.wireMockConfig;

@ExtendWith(WireMockExtension.class)
public class UserServiceTest {
  static WireMockServer wireMockServer = new WireMockServer(
    wireMockConfig().port(8080)
  );

  @Test
  public void testGetUser() {
    stubFor(get(urlEqualTo("/api/users/1"))
      .willReturn(aResponse()
        .withStatus(200)
        .withHeader("Content-Type", "application/json")
        .withBody("{"
          + "\"id\": \"1\","
          + "\"name\": \"John Doe\","
          + "\"email\": \"john@example.com\""
          + "}"
        )));

    UserService service = new UserService("http://localhost:8080");
    User user = service.getUser("1");

    assertThat(user.getName()).isEqualTo("John Doe");
    verify(getRequestedFor(urlEqualTo("/api/users/1")));
  }

  @Test
  public void testUserValidation() {
    stubFor(post(urlEqualTo("/api/users"))
      .withRequestBody(matching(".*missing.*"))
      .willReturn(aResponse()
        .withStatus(400)
        .withBody("{\"error\": \"Missing required fields\"}")));

    UserService service = new UserService("http://localhost:8080");
    Exception exception = assertThrows(Exception.class, () -> {
      service.createUser(new User(null, "Missing"));
    });

    assertThat(exception.getMessage()).contains("required");
  }

  @Test
  public void testRetryLogic() {
    // First 2 calls fail, 3rd succeeds
    stubFor(get(urlEqualTo("/api/users/1"))
      .inScenario("retry")
      .whenScenarioStateIs(Scenario.STARTED)
      .willReturn(aResponse().withStatus(500))
      .willSetStateTo("failed-once"));

    stubFor(get(urlEqualTo("/api/users/1"))
      .inScenario("retry")
      .whenScenarioStateIs("failed-once")
      .willReturn(aResponse().withStatus(500))
      .willSetStateTo("failed-twice"));

    stubFor(get(urlEqualTo("/api/users/1"))
      .inScenario("retry")
      .whenScenarioStateIs("failed-twice")
      .willReturn(aResponse()
        .withStatus(200)
        .withBody("{\"id\": \"1\", \"name\": \"Success\"}")));

    UserService service = new UserService("http://localhost:8080");
    User user = service.getUser("1"); // Retries internally

    assertThat(user.getName()).isEqualTo("Success");
  }
}
```

## Prism - OpenAPI-Based

Prism automatically generates mocks from OpenAPI schemas.

```yaml
# openapi.yaml
openapi: 3.0.0
info:
  title: User API
  version: 1.0.0

servers:
  - url: https://api.example.com
    variables:
      environment:
        default: mock

paths:
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
              examples:
                successful:
                  value:
                    id: "123"
                    name: "John Doe"
                    email: "john@example.com"
        '404':
          description: User not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'

  /users:
    post:
      summary: Create user
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateUserRequest'
      responses:
        '201':
          description: User created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'
        '400':
          description: Invalid input
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'

components:
  schemas:
    User:
      type: object
      required:
        - id
        - name
        - email
      properties:
        id:
          type: string
        name:
          type: string
        email:
          type: string
          format: email
        createdAt:
          type: string
          format: date-time

    CreateUserRequest:
      type: object
      required:
        - name
        - email
      properties:
        name:
          type: string
          minLength: 1
        email:
          type: string
          format: email

    Error:
      type: object
      properties:
        error:
          type: string
```

**Run Prism server**:

```bash
# Install
npm install -g @stoplight/prism-cli

# Start mock server
prism mock openapi.yaml -p 4010

# Now api calls go to http://localhost:4010
curl http://localhost:4010/users/123
```

## Contract-Driven Development

Define API contracts before implementation:

```typescript
// contracts/user-contract.ts
export const userContract = {
  getUser: {
    request: {
      method: 'GET',
      path: '/users/:id'
    },
    response: {
      status: 200,
      body: {
        id: expect.any(String),
        name: expect.any(String),
        email: expect.any(String),
        createdAt: expect.stringMatching(/^\d{4}-\d{2}-\d{2}/)
      }
    }
  },

  createUser: {
    request: {
      method: 'POST',
      path: '/users',
      body: {
        name: expect.any(String),
        email: expect.stringMatching(/@/)
      }
    },
    response: {
      status: 201,
      body: {
        id: expect.any(String),
        name: expect.any(String),
        email: expect.any(String)
      }
    }
  }
};
```

**Frontend test using contract**:

```javascript
import { userContract } from './contracts';

describe('User API Integration', () => {
  it('satisfies user contract', async () => {
    const response = await fetch('http://api.example.com/users', {
      method: 'POST',
      body: JSON.stringify({
        name: 'Test User',
        email: 'test@example.com'
      })
    });

    expect(response.status).toEqual(userContract.createUser.response.status);

    const data = await response.json();
    expect(data).toMatchObject(userContract.createUser.response.body);
  });
});
```

**Backend test using contract**:

```javascript
describe('User API Contract', () => {
  it('satisfies user contract', async () => {
    const response = await request(app)
      .post('/users')
      .send({
        name: 'Test User',
        email: 'test@example.com'
      });

    expect(response.status).toEqual(userContract.createUser.response.status);
    expect(response.body).toMatchObject(userContract.createUser.response.body);
  });
});
```

## Key Takeaways

- **MSW**: Best for JavaScript/React testing, browser-level interception
- **WireMock**: Java/JVM backend testing, stateful scenarios
- **Prism**: Automatic mocks from OpenAPI, great for parallel development
- **Contract-first**: Define API contract before implementation
- **Testing**: Test with mocks, contract, and real services
