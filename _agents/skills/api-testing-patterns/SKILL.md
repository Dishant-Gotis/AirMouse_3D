---
skill_name: api-testing-patterns
description: API testing patterns including contract tests, integration tests, test containers, fixtures
category: Backend Development
version: 1.0.0
---

# API Testing Patterns

## Contract Testing

Ensure API compatibility:

```python
import pytest
import requests
from pydantic import BaseModel

class UserSchema(BaseModel):
  id: int
  email: str
  name: str
  created_at: str

def test_user_schema():
  """Test that API response matches contract"""
  response = requests.get("http://localhost:8000/users/1")

  assert response.status_code == 200

  # Validate against schema
  user = UserSchema(**response.json())
  assert user.id > 0
  assert "@" in user.email

def test_error_contract():
  """Test error response format"""
  response = requests.get("http://localhost:8000/users/999")

  assert response.status_code == 404

  data = response.json()
  assert "code" in data
  assert "message" in data
  assert data["code"] == "NOT_FOUND"

# Using pact for contract testing
from pact import Consumer, Provider

pact = Consumer('UserServiceClient').has_state(
  'User 123 exists'
).upon_receiving(
  'a request for user 123'
).with_request(
  'GET', '/users/123'
).will_respond_with(200, body={
  'id': 123,
  'email': 'user@example.com',
  'name': 'Test User'
})

with pact:
  response = requests.get('http://localhost:8000/users/123')
  assert response.status_code == 200
  data = response.json()
  assert data['id'] == 123
```

## Integration Testing

Test with real dependencies:

```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Use test database
SQLALCHEMY_DATABASE_URL = "sqlite:///test.db"

@pytest.fixture(scope="function")
def test_db():
  engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
  )
  TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
  )

  Base.metadata.create_all(bind=engine)

  def override_get_db():
    db = TestingSessionLocal()
    try:
      yield db
    finally:
      db.close()

  app.dependency_overrides[get_db] = override_get_db

  yield engine

  Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(test_db):
  return TestClient(app)

def test_create_and_read_user(client):
  # Create user
  response = client.post(
    "/users",
    json={"email": "test@example.com", "name": "Test User"}
  )
  assert response.status_code == 201
  user_id = response.json()["id"]

  # Read user
  response = client.get(f"/users/{user_id}")
  assert response.status_code == 200
  assert response.json()["email"] == "test@example.com"

def test_update_user(client):
  # Create
  response = client.post(
    "/users",
    json={"email": "test@example.com", "name": "Test"}
  )
  user_id = response.json()["id"]

  # Update
  response = client.put(
    f"/users/{user_id}",
    json={"name": "Updated"}
  )
  assert response.status_code == 200
  assert response.json()["name"] == "Updated"

def test_delete_user(client):
  # Create
  response = client.post(
    "/users",
    json={"email": "test@example.com", "name": "Test"}
  )
  user_id = response.json()["id"]

  # Delete
  response = client.delete(f"/users/{user_id}")
  assert response.status_code == 204

  # Verify deleted
  response = client.get(f"/users/{user_id}")
  assert response.status_code == 404
```

## Test Containers

Use containerized dependencies:

```python
import pytest
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer
from sqlalchemy import create_engine

@pytest.fixture(scope="session")
def postgres_container():
  container = PostgresContainer("postgres:13")
  container.start()
  yield container
  container.stop()

@pytest.fixture(scope="session")
def redis_container():
  container = RedisContainer("redis:7")
  container.start()
  yield container
  container.stop()

@pytest.fixture
def test_db(postgres_container):
  connection_string = postgres_container.get_connection_url()
  engine = create_engine(connection_string)

  Base.metadata.create_all(bind=engine)

  yield engine

  Base.metadata.drop_all(bind=engine)

@pytest.fixture
def redis_client(redis_container):
  import redis
  return redis.from_url(redis_container.get_connection_url())

def test_with_real_postgres(test_db):
  # Test with real PostgreSQL container
  pass

def test_with_real_redis(redis_client):
  redis_client.set("key", "value")
  assert redis_client.get("key") == b"value"
```

## Fixtures and Factories

Reusable test data:

```python
import pytest
from factory import Factory, Sequence

class UserFactory(Factory):
  class Meta:
    model = User

  id = Sequence(lambda n: n)
  email = Sequence(lambda n: f"user{n}@example.com")
  name = "Test User"

@pytest.fixture
def user():
  return UserFactory()

@pytest.fixture
def users():
  return UserFactory.create_batch(5)

def test_with_factory(client, user):
  response = client.get(f"/users/{user.id}")
  assert response.status_code == 200

def test_with_multiple_users(client, users):
  response = client.get("/users")
  assert len(response.json()) >= 5

# Fixtures with setup/teardown
@pytest.fixture
def user_with_posts(test_db):
  user = User(email="test@example.com", name="Test")
  test_db.add(user)
  test_db.commit()

  for i in range(3):
    post = Post(title=f"Post {i}", author_id=user.id)
    test_db.add(post)
  test_db.commit()

  yield user

  # Cleanup
  test_db.query(Post).filter_by(author_id=user.id).delete()
  test_db.query(User).filter_by(id=user.id).delete()
  test_db.commit()

def test_user_posts(client, user_with_posts):
  response = client.get(f"/users/{user_with_posts.id}/posts")
  assert len(response.json()) == 3
```

## Mock External Services

Test without dependencies:

```python
from unittest.mock import Mock, patch
import requests

@patch('requests.post')
def test_create_user_with_external_service(mock_post):
  # Mock external API response
  mock_post.return_value = Mock(status_code=200, json=lambda: {
    'verification_id': '123'
  })

  # Call endpoint
  response = client.post(
    "/users",
    json={"email": "test@example.com", "name": "Test"}
  )

  assert response.status_code == 201
  mock_post.assert_called_once()

@patch('sendgrid.SendGridAPIClient')
def test_send_email_on_signup(mock_sendgrid):
  mock_sendgrid.return_value.send.return_value = Mock(status_code=202)

  response = client.post(
    "/users",
    json={"email": "test@example.com", "name": "Test"}
  )

  assert response.status_code == 201
  mock_sendgrid.return_value.send.assert_called()

# Using responses library
import responses

@responses.activate
def test_with_mocked_http():
  responses.add(
    responses.GET,
    "https://api.example.com/users/1",
    json={"id": 1, "name": "John"},
    status=200
  )

  response = requests.get("https://api.example.com/users/1")
  assert response.json()["name"] == "John"
```

## Performance Testing

Load testing:

```python
import locust
from locust import HttpUser, task, between

class UserBehavior(HttpUser):
  wait_time = between(1, 3)

  @task(1)
  def get_users(self):
    self.client.get("/users")

  @task(2)
  def get_user(self):
    self.client.get("/users/1")

  @task(1)
  def create_user(self):
    self.client.post("/users", json={
      "email": f"user{random.randint(1,1000)}@example.com",
      "name": "Test"
    })

# Run with: locust -f locustfile.py --host=http://localhost:8000
```

