---
skill_name: api-testing-patterns-2
description: API testing - REST-assured, Supertest, Dredd, schema validation, and Postman collections
category: Testing & Quality
version: 1.0.0
---

# API Testing Patterns

## Supertest for Node.js

Install Supertest:

```bash
npm install -D supertest
```

Basic API tests:

```javascript
import request from 'supertest';
import app from '../app';

describe('API Testing', () => {
  it('should get users', async () => {
    const response = await request(app)
      .get('/api/users')
      .expect(200)
      .expect('Content-Type', /json/);

    expect(Array.isArray(response.body)).toBe(true);
  });

  it('should create user', async () => {
    const response = await request(app)
      .post('/api/users')
      .send({ name: 'John', email: 'john@example.com' })
      .expect(201);

    expect(response.body.id).toBeDefined();
    expect(response.body.name).toBe('John');
  });

  it('should update user', async () => {
    await request(app)
      .patch('/api/users/1')
      .send({ name: 'Jane' })
      .expect(200);
  });

  it('should delete user', async () => {
    await request(app)
      .delete('/api/users/1')
      .expect(204);
  });

  it('should handle validation errors', async () => {
    const response = await request(app)
      .post('/api/users')
      .send({ name: '' })
      .expect(400);

    expect(response.body.error).toBeDefined();
  });
});
```

## REST-assured for Java

Add dependency:

```xml
<dependency>
  <groupId>io.rest-assured</groupId>
  <artifactId>rest-assured</artifactId>
  <version>5.3.1</version>
  <scope>test</scope>
</dependency>
```

Write tests:

```java
import static io.restassured.RestAssured.*;
import static org.hamcrest.Matchers.*;

public class UserApiTest {
  @BeforeAll
  public static void setup() {
    baseURI = "http://localhost:8080";
  }

  @Test
  public void testGetUsers() {
    given()
      .header("Accept", "application/json")
    .when()
      .get("/api/users")
    .then()
      .statusCode(200)
      .body("", hasSize(greaterThan(0)))
      .body("[0].id", notNullValue());
  }

  @Test
  public void testCreateUser() {
    String requestBody = "{\n" +
      "  \"name\": \"John\",\n" +
      "  \"email\": \"john@example.com\"\n" +
      "}";

    given()
      .header("Content-Type", "application/json")
      .body(requestBody)
    .when()
      .post("/api/users")
    .then()
      .statusCode(201)
      .body("id", notNullValue())
      .body("name", equalTo("John"));
  }
}
```

## JSON Schema Validation

Validate API responses:

```javascript
import Ajv from 'ajv';

const ajv = new Ajv();

const userSchema = {
  type: 'object',
  properties: {
    id: { type: 'number' },
    name: { type: 'string' },
    email: { type: 'string', format: 'email' }
  },
  required: ['id', 'name', 'email']
};

const validateUser = ajv.compile(userSchema);

it('should return valid user schema', async () => {
  const response = await request(app).get('/api/users/1');

  const valid = validateUser(response.body);
  expect(valid).toBe(true);
  if (!valid) {
    console.error(validateUser.errors);
  }
});
```

## Dredd API Testing

Create `apiary.apib`:

```markdown
# User API

## Users [/users]

### List Users [GET]

+ Response 200 (application/json)

    + Body

            [
              {
                "id": 1,
                "name": "John",
                "email": "john@example.com"
              }
            ]

### Create User [POST]

+ Request (application/json)

    + Body

            {
              "name": "Jane",
              "email": "jane@example.com"
            }

+ Response 201 (application/json)

    + Body

            {
              "id": 2,
              "name": "Jane",
              "email": "jane@example.com"
            }
```

Run Dredd:

```bash
dredd apiary.apib http://localhost:3000
```

## Postman Collections

Export as JSON:

```json
{
  "info": {
    "name": "User API",
    "version": "1.0"
  },
  "item": [
    {
      "name": "Get Users",
      "request": {
        "method": "GET",
        "url": "{{base_url}}/users"
      },
      "response": []
    },
    {
      "name": "Create User",
      "request": {
        "method": "POST",
        "url": "{{base_url}}/users",
        "body": {
          "mode": "raw",
          "raw": "{\"name\": \"John\", \"email\": \"john@example.com\"}"
        }
      }
    }
  ]
}
```

Run via Newman:

```bash
npm install -g newman
newman run postman_collection.json -e environment.json
```

## Response Assertions

```javascript
it('should validate response structure', async () => {
  const response = await request(app)
    .get('/api/users')
    .expect(200);

  // Check structure
  expect(response.body).toEqual(
    expect.arrayContaining([
      expect.objectContaining({
        id: expect.any(Number),
        name: expect.any(String),
        email: expect.stringMatching(/@/)
      })
    ])
  );
});
```

## Error Response Testing

```javascript
describe('Error Handling', () => {
  it('should return 400 for invalid input', async () => {
    const response = await request(app)
      .post('/api/users')
      .send({ name: '' })
      .expect(400);

    expect(response.body).toHaveProperty('error');
    expect(response.body.error).toMatch(/name/i);
  });

  it('should return 404 for not found', async () => {
    await request(app)
      .get('/api/users/99999')
      .expect(404);
  });

  it('should return 500 for server errors', async () => {
    jest.spyOn(db, 'query').mockRejectedValue(new Error('DB Error'));

    await request(app)
      .get('/api/users')
      .expect(500);
  });
});
```

## Best Practices

1. **Test all HTTP methods** - GET, POST, PUT, PATCH, DELETE
2. **Validate response schemas** - Use JSON Schema validation
3. **Test error cases** - 400, 404, 500 responses
4. **Use environment variables** - Base URLs, API keys
5. **Test authentication** - Bearer tokens, API keys
6. **Mock external calls** - Keep tests isolated
7. **Parameterize tests** - Test multiple scenarios
8. **Automate in CI** - Run API tests on every commit
