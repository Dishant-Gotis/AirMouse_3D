---
skill_name: API Documentation Guide
description: Create comprehensive API documentation with OpenAPI specs, Swagger UI, Redoc, code examples, and versioning strategies
category: API & Integration
version: 1.0.0
---

# API Documentation Guide

## Overview
Good documentation is critical for API adoption. Master OpenAPI, Swagger, and best practices for developer experience.

## OpenAPI 3.0 Specification

```yaml
openapi: 3.0.0
info:
  title: User Management API
  description: API for managing users and posts
  version: 1.0.0
  contact:
    name: API Support
    email: support@example.com
  license:
    name: MIT

servers:
  - url: https://api.example.com/v1
    description: Production server
  - url: https://staging.example.com/v1
    description: Staging server

paths:
  /users:
    get:
      summary: List all users
      description: Retrieve a paginated list of users
      operationId: listUsers
      tags:
        - Users
      parameters:
        - name: page
          in: query
          description: Page number
          schema:
            type: integer
            default: 1
        - name: limit
          in: query
          description: Items per page
          schema:
            type: integer
            default: 20
            maximum: 100
        - name: status
          in: query
          description: Filter by status
          schema:
            type: string
            enum: [active, inactive, banned]
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserList'
        '400':
          description: Bad request
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '401':
          description: Unauthorized
      security:
        - bearerAuth: []

    post:
      summary: Create a new user
      operationId: createUser
      tags:
        - Users
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

  /users/{userId}:
    get:
      summary: Get user by ID
      operationId: getUser
      tags:
        - Users
      parameters:
        - name: userId
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

    put:
      summary: Update user
      operationId: updateUser
      tags:
        - Users
      parameters:
        - name: userId
          in: path
          required: true
          schema:
            type: string
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UpdateUserRequest'
      responses:
        '200':
          description: User updated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'

components:
  schemas:
    User:
      type: object
      required:
        - id
        - username
        - email
      properties:
        id:
          type: string
          format: uuid
        username:
          type: string
          minLength: 3
          maxLength: 50
        email:
          type: string
          format: email
        status:
          type: string
          enum: [active, inactive, banned]
        createdAt:
          type: string
          format: date-time
        updatedAt:
          type: string
          format: date-time

    CreateUserRequest:
      type: object
      required:
        - username
        - email
        - password
      properties:
        username:
          type: string
          minLength: 3
          maxLength: 50
        email:
          type: string
          format: email
        password:
          type: string
          format: password
          minLength: 8

    UpdateUserRequest:
      type: object
      properties:
        username:
          type: string
        email:
          type: string
          format: email
        status:
          type: string
          enum: [active, inactive]

    UserList:
      type: object
      properties:
        data:
          type: array
          items:
            $ref: '#/components/schemas/User'
        pagination:
          type: object
          properties:
            page:
              type: integer
            limit:
              type: integer
            total:
              type: integer
            pages:
              type: integer

    Error:
      type: object
      required:
        - code
        - message
      properties:
        code:
          type: string
        message:
          type: string
        details:
          type: object

  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

  responses:
    NotFound:
      description: Resource not found
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'

    Unauthorized:
      description: Unauthorized
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
```

## Swagger UI Integration

```python
from flask import Flask
from flask_restx import Api, Resource, fields, Namespace

app = Flask(__name__)
api = Api(app, version='1.0', title='User Management API',
    description='API for managing users',
    doc='/docs')

ns = api.namespace('users', description='User operations')

# Define models
user_model = api.model('User', {
    'id': fields.String(required=True),
    'username': fields.String(required=True),
    'email': fields.String(required=True),
    'status': fields.String(enum=['active', 'inactive'])
})

@ns.route('/')
class UserList(Resource):
    @ns.doc('list_users')
    @ns.marshal_list_with(user_model)
    def get(self):
        '''Get all users'''
        return []

    @ns.doc('create_user')
    @ns.expect(user_model)
    @ns.marshal_with(user_model, code=201)
    def post(self):
        '''Create a new user'''
        return {}, 201

@ns.route('/<id>')
class User(Resource):
    @ns.doc('get_user')
    @ns.marshal_with(user_model)
    def get(self, id):
        '''Get user by ID'''
        return {}
```

## Code Examples

### Example Requests

```bash
# List users
curl -X GET https://api.example.com/v1/users \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Accept: application/json"

# Create user
curl -X POST https://api.example.com/v1/users \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "secure_password"
  }'

# Update user
curl -X PUT https://api.example.com/v1/users/123 \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "inactive"
  }'
```

### Code Examples

```python
import requests

# Initialize client
BASE_URL = "https://api.example.com/v1"
headers = {
    "Authorization": "Bearer YOUR_TOKEN",
    "Content-Type": "application/json"
}

# Get users
response = requests.get(f"{BASE_URL}/users", headers=headers)
users = response.json()

# Create user
user_data = {
    "username": "john_doe",
    "email": "john@example.com",
    "password": "secure_password"
}
response = requests.post(f"{BASE_URL}/users", json=user_data, headers=headers)
new_user = response.json()

# Update user
update_data = {"status": "inactive"}
response = requests.put(f"{BASE_URL}/users/123", json=update_data, headers=headers)
```

## Redoc Documentation

```html
<!DOCTYPE html>
<html>
  <head>
    <title>API Documentation</title>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700" rel="stylesheet">
    <style>
      body {
        margin: 0;
        padding: 0;
      }
    </style>
  </head>
  <body>
    <redoc spec-url='https://api.example.com/openapi.json'></redoc>
    <script src="https://cdn.jsdelivr.net/npm/redoc@latest/bundles/redoc.standalone.js"> </script>
  </body>
</html>
```

## Production Checklist

- [ ] Create OpenAPI 3.0 spec
- [ ] Document all endpoints
- [ ] Include request/response examples
- [ ] Document error codes
- [ ] Describe authentication methods
- [ ] Document rate limits
- [ ] Generate Swagger UI
- [ ] Version documentation with API
- [ ] Keep examples up to date
- [ ] Include changelog/migration guides
