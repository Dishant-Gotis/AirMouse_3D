---
skill_name: backend-integration-testing
description: Backend integration testing - real DBs with TestContainers, service wiring, and cleanup
category: Testing & Quality
version: 1.0.0
---

# Backend Integration Testing

## TestContainers Setup

Install TestContainers:

```bash
npm install -D testcontainers
```

PostgreSQL container test:

```typescript
import { PostgreSqlContainer } from 'testcontainers';
import { DataSource } from 'typeorm';
import { User } from './entities/User';

describe('User Repository Integration', () => {
  let container;
  let dataSource: DataSource;

  beforeAll(async () => {
    container = await new PostgreSqlContainer()
      .withDatabase('testdb')
      .withUsername('testuser')
      .withUserPassword('testpass')
      .start();

    dataSource = new DataSource({
      type: 'postgres',
      host: container.getHost(),
      port: container.getPort(),
      database: 'testdb',
      username: 'testuser',
      password: 'testpass',
      entities: [User],
      synchronize: true
    });

    await dataSource.initialize();
  });

  afterAll(async () => {
    await dataSource.destroy();
    await container.stop();
  });

  it('should create and find user', async () => {
    const userRepository = dataSource.getRepository(User);

    const user = new User();
    user.email = 'test@example.com';
    user.name = 'Test User';

    await userRepository.save(user);

    const found = await userRepository.findOne({
      where: { email: 'test@example.com' }
    });

    expect(found?.name).toBe('Test User');
  });
});
```

## Multi-Container Setup

```typescript
import { PostgreSqlContainer, RedisContainer } from 'testcontainers';

describe('Service Integration with Multiple Containers', () => {
  let postgres, redis;
  let dataSource, redisClient;

  beforeAll(async () => {
    // Start PostgreSQL
    postgres = await new PostgreSqlContainer()
      .withDatabase('testdb')
      .withUsername('user')
      .withUserPassword('pass')
      .start();

    // Start Redis
    redis = await new RedisContainer()
      .start();

    // Initialize connections
    dataSource = new DataSource({
      type: 'postgres',
      host: postgres.getHost(),
      port: postgres.getPort(),
      database: 'testdb',
      username: 'user',
      password: 'pass',
      entities: [User, Post],
      synchronize: true
    });

    await dataSource.initialize();

    redisClient = redis.getClient();
  });

  afterAll(async () => {
    await dataSource.destroy();
    await postgres.stop();
    await redis.stop();
  });

  it('should cache user data', async () => {
    const userService = new UserService(dataSource, redisClient);

    // First call - from database
    const user1 = await userService.getUser(1);
    expect(user1.name).toBe('John');

    // Second call - from cache
    const cachedUser = await redisClient.get('user:1');
    expect(cachedUser).toBeDefined();

    const user2 = await userService.getUser(1);
    expect(user2.name).toBe('John');
  });
});
```

## Service Wiring Tests

```typescript
describe('Service Integration', () => {
  let userService: UserService;
  let userRepository: Repository<User>;
  let emailService: EmailService;
  let dataSource: DataSource;

  beforeEach(async () => {
    // Setup database
    const postgres = await new PostgreSqlContainer().start();

    dataSource = new DataSource({
      type: 'postgres',
      host: postgres.getHost(),
      port: postgres.getPort(),
      database: 'testdb',
      username: 'test',
      password: 'test',
      entities: [User],
      synchronize: true
    });

    await dataSource.initialize();
    userRepository = dataSource.getRepository(User);

    // Setup services
    emailService = new FakeEmailService();
    userService = new UserService(userRepository, emailService);
  });

  afterEach(async () => {
    await dataSource.destroy();
  });

  it('should wire services correctly', async () => {
    // Act
    const user = await userService.createUser({
      email: 'user@example.com',
      name: 'Test'
    });

    // Assert - service created user
    expect(user.id).toBeDefined();

    // Assert - email was sent
    const emails = await emailService.getSent();
    expect(emails).toHaveLength(1);
    expect(emails[0].to).toBe('user@example.com');
  });

  it('should handle transaction rollback', async () => {
    try {
      await dataSource.transaction(async (em) => {
        const user = new User();
        user.email = 'fail@example.com';
        await em.save(user);

        // Simulate error
        throw new Error('Simulated failure');
      });
    } catch (error) {
      // Expected
    }

    // Verify rollback
    const user = await userRepository.findOne({
      where: { email: 'fail@example.com' }
    });

    expect(user).toBeUndefined();
  });
});
```

## Database Fixture Loading

```typescript
describe('With Database Fixtures', () => {
  let dataSource: DataSource;

  beforeAll(async () => {
    const postgres = await new PostgreSqlContainer().start();

    dataSource = new DataSource({
      type: 'postgres',
      host: postgres.getHost(),
      port: postgres.getPort(),
      database: 'testdb',
      username: 'test',
      password: 'test',
      entities: [User, Post],
      synchronize: true
    });

    await dataSource.initialize();
  });

  beforeEach(async () => {
    // Load fixtures
    const users = [
      { id: 1, email: 'user1@example.com', name: 'User 1' },
      { id: 2, email: 'user2@example.com', name: 'User 2' }
    ];

    const userRepository = dataSource.getRepository(User);
    await userRepository.insert(users);
  });

  afterEach(async () => {
    // Clean up
    const userRepository = dataSource.getRepository(User);
    await userRepository.query('TRUNCATE users CASCADE');
  });

  it('should query fixture data', async () => {
    const userRepository = dataSource.getRepository(User);
    const users = await userRepository.find();

    expect(users).toHaveLength(2);
  });
});
```

## Cleanup Strategies

```typescript
describe('Cleanup Best Practices', () => {
  let dataSource: DataSource;

  beforeAll(async () => {
    // Initialize once
    dataSource = setupDataSource();
    await dataSource.initialize();
  });

  afterAll(async () => {
    // Clean up once
    await dataSource.destroy();
  });

  beforeEach(async () => {
    // Truncate tables before each test
    await dataSource.query('TRUNCATE users, posts CASCADE');
  });

  afterEach(async () => {
    // Verify cleanup
    const userCount = await dataSource
      .query('SELECT COUNT(*) as count FROM users');
    expect(userCount[0].count).toBe('0');
  });

  it('should not pollute database', async () => {
    const userRepository = dataSource.getRepository(User);
    const user = new User();
    user.email = 'test@example.com';
    await userRepository.save(user);

    const count = await userRepository.count();
    expect(count).toBe(1);
  });
});
```

## Best Practices

1. **Use TestContainers** - Lightweight, isolated databases
2. **Share containers** - One container per suite, not per test
3. **Async cleanup** - Properly await teardown
4. **Fixtures efficiently** - Batch insert, not individual
5. **Transaction testing** - Verify rollback behavior
6. **Service wiring** - Test full dependency chains
7. **Real databases** - Don't mock in integration tests
8. **Isolation** - Tests independent of each other
