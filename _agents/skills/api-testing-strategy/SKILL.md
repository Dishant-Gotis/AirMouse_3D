---
skill_name: API Testing Strategy
description: Test APIs with Postman, Newman, contract testing, API mocking, and CI/CD integration for reliability
category: API & Integration
version: 1.0.0
---

# API Testing Strategy

## Overview
Comprehensive API testing ensures reliability. Master tools and approaches for automated testing and contract validation.

## Unit Tests with Pytest

```python
import pytest
import json
from app import create_app
from models import User, Post

@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        yield app

@pytest.fixture
def client(app):
    return app.test_client()

class TestUserAPI:
    def test_list_users_success(self, client):
        response = client.get('/api/v1/users')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'data' in data
        assert isinstance(data['data'], list)

    def test_list_users_pagination(self, client):
        response = client.get('/api/v1/users?page=1&limit=10')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['pagination']['page'] == 1
        assert data['pagination']['limit'] == 10

    def test_create_user_success(self, client):
        user_data = {
            'username': 'john_doe',
            'email': 'john@example.com',
            'password': 'secure_password'
        }
        response = client.post('/api/v1/users', json=user_data)
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['username'] == 'john_doe'
        assert 'id' in data

    def test_create_user_validation_error(self, client):
        user_data = {
            'username': 'ab',  # Too short
            'email': 'invalid'  # Invalid email
        }
        response = client.post('/api/v1/users', json=user_data)
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_get_user_not_found(self, client):
        response = client.get('/api/v1/users/nonexistent')
        assert response.status_code == 404

    def test_update_user_success(self, client):
        # Create user first
        user_data = {'username': 'john', 'email': 'john@example.com', 'password': 'pass'}
        create_resp = client.post('/api/v1/users', json=user_data)
        user_id = create_resp.json['id']

        # Update user
        update_data = {'status': 'inactive'}
        response = client.put(f'/api/v1/users/{user_id}', json=update_data)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'inactive'

    def test_delete_user_success(self, client):
        # Create and delete
        user_data = {'username': 'temp', 'email': 'temp@example.com', 'password': 'pass'}
        create_resp = client.post('/api/v1/users', json=user_data)
        user_id = create_resp.json['id']

        response = client.delete(f'/api/v1/users/{user_id}')
        assert response.status_code == 204
```

## Contract Testing

```python
from pact import Consumer, Provider, Term
import re

pact = Consumer('Mobile Client').has_state(
    'user with id 123 exists'
).upon_receiving(
    'a request for user details'
).with_request(
    'GET', '/users/123'
).will_respond_with(
    200,
    body={
        'id': 123,
        'username': Term(
            r'^\w+$',  # Alphanumeric
            'john_doe'
        ),
        'email': Term(
            r'^.+@.+\..+$',
            'john@example.com'
        )
    }
)

# Verify contract
with pact:
    response = requests.get('http://localhost:5000/users/123')
    assert response.status_code == 200
    data = response.json()
    assert data['id'] == 123
    assert isinstance(data['username'], str)
```

## API Mocking

```python
from unittest.mock import Mock, patch
import responses

# Mock external API
@responses.activate
def test_with_mock_api():
    responses.add(
        responses.GET,
        'https://api.example.com/users/123',
        json={'id': 123, 'name': 'John'},
        status=200
    )

    response = requests.get('https://api.example.com/users/123')
    assert response.json()['name'] == 'John'

# Mock in tests
def test_payment_processing(client):
    with patch('stripe.Charge.create') as mock_stripe:
        mock_stripe.return_value = {'id': 'ch_123', 'status': 'succeeded'}

        response = client.post('/api/charge', json={'amount': 100})
        assert response.status_code == 200
```

## Postman Testing

```json
{
  "info": {
    "name": "User API Tests",
    "version": "1.0.0"
  },
  "item": [
    {
      "name": "Create User",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\"username\": \"john\", \"email\": \"john@example.com\", \"password\": \"pass\"}"
        },
        "url": {
          "raw": "{{base_url}}/users",
          "host": ["{{base_url}}"],
          "path": ["users"]
        }
      },
      "event": [
        {
          "listen": "test",
          "script": {
            "exec": [
              "pm.test('Status code is 201', function() {",
              "  pm.response.to.have.status(201);",
              "});",
              "pm.test('Response has user id', function() {",
              "  var jsonData = pm.response.json();",
              "  pm.expect(jsonData.id).to.exist;",
              "});",
              "pm.environment.set('user_id', pm.response.json().id);"
            ]
          }
        }
      ]
    }
  ]
}
```

## Newman CI/CD

```bash
# Run Postman collection
newman run collection.json \
  --environment environment.json \
  --reporters cli,json \
  --reporter-json-export results.json

# With threshold
newman run collection.json \
  -e environment.json \
  --global-var "base_url=https://api.example.com" \
  --timeout-request 5000 \
  --timeout-script 5000
```

## CI/CD Integration

```yaml
# .github/workflows/api-tests.yml
name: API Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: password

    steps:
      - uses: actions/checkout@v2

      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run unit tests
        run: pytest tests/ -v --cov

      - name: Upload coverage
        uses: codecov/codecov-action@v2

      - name: Run API integration tests
        run: pytest tests/api/ -v

      - name: Run Postman tests
        run: |
          npm install -g newman
          newman run postman_collection.json \
            --environment postman_environment.json \
            --reporters cli,json
```

## Production Checklist

- [ ] Write unit tests for all endpoints
- [ ] Implement contract testing
- [ ] Test error scenarios
- [ ] Validate response schemas
- [ ] Test rate limiting behavior
- [ ] Test authentication flows
- [ ] Load test critical endpoints
- [ ] Mock external dependencies
- [ ] Automate in CI/CD pipeline
- [ ] Monitor test coverage
