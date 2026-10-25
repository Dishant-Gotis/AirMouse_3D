---
skill_name: bdd-patterns
description: BDD patterns - Gherkin syntax, step definitions, living documentation, Cucumber, and SpecFlow
category: Testing & Quality
version: 1.0.0
---

# BDD Patterns

## Gherkin Syntax

Write `features/user-login.feature`:

```gherkin
Feature: User Login
  As a user
  I want to log in to the application
  So that I can access my account

  Background:
    Given the application is open
    And there is a user with email "user@example.com" and password "password123"

  Scenario: Successful login
    Given I am on the login page
    When I enter email "user@example.com"
    And I enter password "password123"
    And I click the login button
    Then I should be redirected to the dashboard
    And I should see "Welcome" message

  Scenario: Invalid credentials
    Given I am on the login page
    When I enter email "user@example.com"
    And I enter password "wrongpassword"
    And I click the login button
    Then I should see error message "Invalid credentials"
    And I should remain on login page

  Scenario Outline: Login with various credentials
    Given I am on the login page
    When I enter email "<email>"
    And I enter password "<password>"
    And I click the login button
    Then the result should be "<result>"

    Examples:
      | email             | password    | result          |
      | user@example.com  | password123 | success         |
      | user@example.com  | wrong       | invalid         |
      | invalid@example   | password123 | invalid_email   |
      | missing@example   | password123 | user_not_found  |
```

## Step Definitions

Create `features/step_definitions/login-steps.js`:

```javascript
import { Given, When, Then, Before, After } from '@cucumber/cucumber';
import { expect } from '@jest/globals';
import LoginPage from '../../pages/LoginPage';
import app from '../../app';

let loginPage;
let browser;
let response;

Before(function() {
  // Initialize before each scenario
  loginPage = new LoginPage();
});

After(function() {
  // Cleanup after each scenario
  browser?.close();
});

Given('the application is open', async function() {
  browser = await loginPage.open();
});

Given('there is a user with email {string} and password {string}', async function(email, password) {
  await app.db.users.create({
    email,
    password: await app.hashPassword(password),
    name: 'Test User'
  });
});

Given('I am on the login page', async function() {
  await loginPage.navigate();
  expect(await loginPage.isVisible()).toBe(true);
});

When('I enter email {string}', async function(email) {
  await loginPage.fillEmail(email);
});

When('I enter password {string}', async function(password) {
  await loginPage.fillPassword(password);
});

When('I click the login button', async function() {
  response = await loginPage.submit();
});

Then('I should be redirected to the dashboard', async function() {
  const url = await loginPage.getCurrentUrl();
  expect(url).toMatch(/\/dashboard/);
});

Then('I should see {string} message', async function(message) {
  const text = await loginPage.getText('.welcome-message');
  expect(text).toContain(message);
});

Then('I should see error message {string}', async function(message) {
  const error = await loginPage.getErrorMessage();
  expect(error).toContain(message);
});

Then('I should remain on login page', async function() {
  const url = await loginPage.getCurrentUrl();
  expect(url).toMatch(/\/login/);
});

Then('the result should be {string}', function(expectedResult) {
  expect(response.status).toBeDefined();
  // Assert based on result
});
```

## Living Documentation

Generate reports from feature files:

```bash
npm install -D @cucumber/cucumber
npx cucumber-js features --publish
```

HTML reports:

```bash
npm install -D cucumber-html-reporter
npx cucumber-js features --format json:test_results.json
node generate-report.js
```

## Advanced Hooks

```javascript
import { setDefaultTimeout, BeforeAll, AfterAll } from '@cucumber/cucumber';

setDefaultTimeout(60 * 1000);

BeforeAll(async function() {
  // Database setup
  await database.connect();
  await database.migrate();
});

AfterAll(async function() {
  // Database cleanup
  await database.disconnect();
});

Before(function(scenario) {
  console.log(`Starting: ${scenario.gherkinDocument.feature.name}`);
});

After(async function(scenario) {
  if (scenario.result.status === 'FAILED') {
    const screenshot = await page.screenshot();
    this.attach(screenshot, 'image/png');
  }
});
```

## Data Tables

```gherkin
Scenario: Create multiple users
  Given the following users exist:
    | email           | name    | role  |
    | admin@test.com  | Admin   | admin |
    | user@test.com   | User    | user  |
    | guest@test.com  | Guest   | guest |
  When I navigate to the users page
  Then I should see 3 users listed
```

Step implementation:

```javascript
Given('the following users exist:', async function(dataTable) {
  const users = dataTable.hashes();

  for (const user of users) {
    await app.db.users.create({
      email: user.email,
      name: user.name,
      role: user.role
    });
  }
});
```

## Tags for Selective Execution

```gherkin
@smoke
Feature: Login

  @critical
  Scenario: Successful login
    ...

  @slow
  @regression
  Scenario: Invalid credentials
    ...
```

Run specific tags:

```bash
npx cucumber-js --tags "@smoke"
npx cucumber-js --tags "@critical and not @slow"
npx cucumber-js --tags "@regression or @smoke"
```

## CI/CD Integration

GitHub Actions:

```yaml
name: BDD Tests

on: [push, pull_request]

jobs:
  bdd:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
      - run: npm ci

      - name: Run BDD tests
        run: npm run test:bdd

      - name: Generate report
        if: always()
        run: npm run report:bdd

      - name: Upload report
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: bdd-report
          path: cucumber-report.html

      - name: Comment PR
        if: failure()
        uses: actions/github-script@v6
        with:
          script: |
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: 'BDD tests failed. See artifact for details.'
            });
```

## Best Practices

1. **Business language** - Use non-technical terms
2. **Single responsibility** - One scenario per behavior
3. **Clear steps** - Avoid implementation details
4. **Reusable steps** - DRY up step definitions
5. **Data-driven** - Use scenario outlines
6. **Living documentation** - Keep features current
7. **Avoid GUI testing** - Focus on behavior
8. **Tag scenarios** - Organize for CI/CD
