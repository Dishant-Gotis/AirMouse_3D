---
skill_name: artillery-load-testing
description: Artillery load testing - scenarios, phases, processors, custom metrics, and CI integration
category: Testing & Quality
version: 1.0.0
---

# Artillery Load Testing

## Installation and Basic Configuration

Install Artillery:

```bash
npm install -D artillery
```

Create `load-test.yml`:

```yaml
config:
  target: "https://api.example.com"
  phases:
    - duration: 60
      arrivalRate: 10
      name: "Warm up"
    - duration: 120
      arrivalRate: 20
      name: "Ramp up"
    - duration: 60
      arrivalRate: 30
      name: "Spike"
  processor: "./processor.js"

scenarios:
  - name: "User API Flow"
    flow:
      - get:
          url: "/users"
          expect:
            - statusCode: 200

  - name: "Create User"
    flow:
      - post:
          url: "/users"
          json:
            name: "{{ name }}"
            email: "{{ email }}"
          expect:
            - statusCode: 201
            - contentType: json
```

Run test:

```bash
artillery run load-test.yml
artillery run --target https://api.example.com load-test.yml
```

## Advanced Scenarios

Create complex user flows:

```yaml
scenarios:
  - name: "Complete User Journey"
    flow:
      # Login
      - post:
          url: "/auth/login"
          json:
            username: "testuser"
            password: "password"
          capture:
            json: "$.token"
            as: "authToken"
          expect:
            - statusCode: 200

      # Get profile
      - get:
          url: "/user/profile"
          headers:
            Authorization: "Bearer {{ authToken }}"
          expect:
            - statusCode: 200

      # Update profile
      - patch:
          url: "/user/profile"
          json:
            firstName: "Updated"
            lastName: "User"
          headers:
            Authorization: "Bearer {{ authToken }}"
          expect:
            - statusCode: 200

      # Get updated profile
      - get:
          url: "/user/profile"
          headers:
            Authorization: "Bearer {{ authToken }}"
          expect:
            - statusCode: 200

      # Logout
      - post:
          url: "/auth/logout"
          headers:
            Authorization: "Bearer {{ authToken }}"
```

## Processors for Custom Logic

Create `processor.js`:

```javascript
module.exports = {
  beforeRequest: beforeRequestHandler,
  afterResponse: afterResponseHandler,
  generatePayload: generatePayloadHandler,
};

function beforeRequestHandler(requestParams, context, ee, next) {
  // Add custom headers
  requestParams.headers['X-Custom-Header'] = 'CustomValue';

  // Add timestamp
  requestParams.json = requestParams.json || {};
  requestParams.json.timestamp = new Date().toISOString();

  return next();
}

function afterResponseHandler(requestParams, response, context, ee, next) {
  // Log response time
  console.log(`Response time: ${response.timings.total}ms`);

  // Emit custom event
  if (response.statusCode === 500) {
    ee.emit('error', 'Server error encountered');
  }

  // Extract data for next request
  if (response.statusCode === 200) {
    context.vars.lastId = response.body.id;
  }

  return next();
}

function generatePayloadHandler(context) {
  return {
    name: `User${Math.random().toString(36).substr(2, 9)}`,
    email: `user${Date.now()}@example.com`,
  };
}
```

Use processor in config:

```yaml
config:
  processor: "./processor.js"

scenarios:
  - name: "Custom Processing"
    flow:
      - post:
          url: "/users"
          json:
            "{{ generatePayload() }}"
          expect:
            - statusCode: 201
```

## Multiple Scenarios with Weights

```yaml
scenarios:
  - name: "Browse Products"
    weight: 70
    flow:
      - get:
          url: "/products"
      - get:
          url: "/products/{{ productId }}"

  - name: "Add to Cart"
    weight: 20
    flow:
      - post:
          url: "/cart"
          json:
            productId: "{{ productId }}"
            quantity: 1

  - name: "Checkout"
    weight: 10
    flow:
      - post:
          url: "/checkout"
          json:
            cartId: "{{ cartId }}"
```

## Custom Metrics and Assertions

```yaml
config:
  target: "https://api.example.com"
  phases:
    - duration: 120
      arrivalRate: 10

scenarios:
  - name: "Metrics Test"
    flow:
      - get:
          url: "/api/data"
          expect:
            - statusCode: 200
            - contentType: json
            - hasProperty: data
            - matchesRegexp: "^[a-z]"
            - think: 5  # Think time: 5 seconds
          capture:
            json: "$.data.length"
            as: "dataCount"

      # Conditional based on captured value
      - loop:
          - get:
              url: "/api/item/{{ itemId }}"
        count: "{{ dataCount }}"

      # Timeout configuration
      - get:
          url: "/slow-endpoint"
          timeout: 30000  # 30 second timeout
```

## Setup and Teardown

```javascript
// processor.js with setup/teardown
module.exports = {
  setup: setupHandler,
  teardown: teardownHandler,
  beforeRequest: beforeRequestHandler,
};

function setupHandler(context, ee, next) {
  console.log('Load test starting...');
  context.vars.startTime = Date.now();
  return next();
}

function teardownHandler(context, ee, next) {
  const duration = Date.now() - context.vars.startTime;
  console.log(`Load test completed in ${duration}ms`);
  return next();
}

function beforeRequestHandler(requestParams, context, ee, next) {
  // Add request ID for tracking
  requestParams.headers['X-Request-ID'] = `${Date.now()}-${Math.random()}`;
  return next();
}
```

## CI Integration with GitHub Actions

```yaml
# .github/workflows/load-test.yml
name: Load Testing

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM
  workflow_dispatch:

jobs:
  load-test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - uses: actions/setup-node@v3
        with:
          node-version: '18'

      - run: npm ci

      - name: Run load test
        run: |
          artillery run load-test.yml --output results.json

      - name: Generate HTML report
        run: |
          artillery report results.json

      - name: Upload report
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: load-test-report
          path: artillery-report.html

      - name: Check thresholds
        run: |
          if grep -q "p95 > 5000" results.json; then
            echo "Performance threshold exceeded!"
            exit 1
          fi
```

## Realistic Test Data

```yaml
config:
  processor: "./processor.js"
  variables:
    products:
      - { id: 1, name: "Widget" }
      - { id: 2, name: "Gadget" }
      - { id: 3, name: "Doohickey" }
    users:
      - { id: 1, name: "Alice" }
      - { id: 2, name: "Bob" }

scenarios:
  - name: "Browse Products"
    flow:
      - get:
          url: "/products/{{ products[0].id }}"
      - get:
          url: "/products/{{ products[1].id }}"
      - post:
          url: "/cart"
          json:
            userId: "{{ users[0].id }}"
            productId: "{{ products[0].id }}"
```

## Reporting

Generate and analyze reports:

```bash
# Run test with JSON output
artillery run load-test.yml --output results.json

# Generate HTML report
artillery report results.json

# Print summary
artillery run load-test.yml

# Compare test runs
artillery compare results1.json results2.json
```

## Best Practices

1. **Define realistic phases** - Ramp, constant load, spike
2. **Use processors** - Customize behavior and data
3. **Capture and reuse data** - From responses in later requests
4. **Weight scenarios** - Reflect actual user traffic patterns
5. **Monitor thresholds** - Check error rates and latency
6. **Test regularly** - Schedule baseline tests
7. **Analyze results** - Compare runs over time
8. **Clean up resources** - Use teardown for cleanup
