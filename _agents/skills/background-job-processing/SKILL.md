---
title: Background Job Processing & Scheduling
description: Master BullMQ, Celery, Sidekiq patterns, retry strategies, and job monitoring
author: Claude Skills 360
date: 2026-03-17
category: Backend
tags: [Jobs, Queues, Scheduling, Background Processing, BullMQ]
skill_level: Intermediate
estimated_time: 45 minutes
---

# Background Job Processing & Scheduling

## BullMQ (Node.js)

### Queue Setup and Job Processing
Create and process background jobs:

```javascript
import { Queue, Worker } from 'bullmq';
import redis from 'redis';

const redisClient = redis.createClient();

// Create queue
const emailQueue = new Queue('emails', {
  connection: redisClient,
  defaultJobOptions: {
    attempts: 3,
    backoff: {
      type: 'exponential',
      delay: 2000,
    },
    removeOnComplete: { age: 3600 }, // Keep 1 hour
  },
});

// Add jobs to queue
async function sendWelcomeEmail(userId) {
  await emailQueue.add(
    'welcome',
    { userId },
    {
      priority: 10, // High priority
      delay: 5000, // Delay 5 seconds
      jobId: `welcome-${userId}`, // Prevent duplicates
    }
  );
}

// Process jobs
const emailWorker = new Worker('emails', async (job) => {
  console.log(`Processing ${job.name} for user ${job.data.userId}`);

  try {
    const user = await getUser(job.data.userId);
    await sendEmail(user.email, 'Welcome!', welcomeTemplate);

    return { success: true, timestamp: new Date() };
  } catch (error) {
    // Automatic retry happens here
    throw error;
  }
}, {
  connection: redisClient,
  concurrency: 5, // Process 5 jobs simultaneously
});

// Job event handlers
emailWorker.on('completed', (job) => {
  console.log(`Job ${job.id} completed`);
});

emailWorker.on('failed', (job, error) => {
  console.error(`Job ${job.id} failed after ${job.attemptsMade} attempts:`, error.message);
});

emailWorker.on('active', (job) => {
  console.log(`Processing job ${job.id}`);
});
```

### Scheduled Jobs
Schedule recurring jobs with cron:

```javascript
// Import cron expressions
import cron from 'cron';

// Create repeating queue
const reportQueue = new Queue('reports', { connection: redisClient });

// Schedule job to run every day at 2 AM
await reportQueue.add(
  'daily-report',
  {},
  {
    repeat: {
      pattern: '0 2 * * *', // Cron expression
    },
  }
);

// Schedule with specific timing
await reportQueue.add(
  'weekly-summary',
  {},
  {
    repeat: {
      every: 7 * 24 * 60 * 60 * 1000, // Every 7 days
    },
  }
);

// Process scheduled reports
const reportWorker = new Worker('reports', async (job) => {
  if (job.name === 'daily-report') {
    const report = await generateDailyReport();
    await sendReport(report);
  }
}, { connection: redisClient });
```

### Retry Strategies
Implement sophisticated retry logic:

```javascript
const dataQueue = new Queue('data-sync', {
  connection: redisClient,
  defaultJobOptions: {
    attempts: 5,
    backoff: {
      type: 'custom',
      delay: (attemptsMade) => {
        // Exponential with jitter
        const baseDelay = Math.pow(2, attemptsMade) * 1000;
        const jitter = Math.random() * 1000;
        return baseDelay + jitter;
      },
    },
  },
});

// Custom retry logic
const dataWorker = new Worker('data-sync', async (job) => {
  try {
    await syncDataFromAPI();
  } catch (error) {
    // Don't retry on validation errors
    if (error.statusCode === 400) {
      console.error('Validation error, not retrying:', error.message);
      throw new Error(`STOP: ${error.message}`); // Stop retries
    }

    // Retry on transient errors
    if (error.statusCode >= 500 || error.code === 'ECONNREFUSED') {
      throw error; // Trigger retry
    }

    throw new Error(`STOP: ${error.message}`);
  }
}, { connection: redisClient });

// Exponential backoff with maximum delay
const backoffConfig = {
  type: 'exponential',
  delay: 2000,
  options: {
    maxDelay: 60000, // Cap at 60 seconds
  },
};
```

## Job Monitoring

### Queue Statistics and Metrics
Monitor job processing:

```javascript
// Get queue stats
async function getQueueStats(queueName) {
  const queue = new Queue(queueName, { connection: redisClient });

  const counts = await queue.getJobCounts();
  const isPaused = await queue.isPaused();

  return {
    waiting: counts.waiting,
    active: counts.active,
    completed: counts.completed,
    failed: counts.failed,
    delayed: counts.delayed,
    paused: isPaused,
  };
}

// Get failed jobs
async function getFailedJobs(queueName) {
  const queue = new Queue(queueName, { connection: redisClient });
  const failed = await queue.getFailed(0, -1);

  return failed.map(job => ({
    id: job.id,
    name: job.name,
    data: job.data,
    error: job.failedReason,
    attempts: job.attemptsMade,
    stacktrace: job.stacktrace,
  }));
}

// Retry failed jobs
async function retryFailedJobs(queueName, limit = 10) {
  const queue = new Queue(queueName, { connection: redisClient });
  const failed = await queue.getFailed(0, limit - 1);

  for (const job of failed) {
    await job.retry();
  }

  return { retried: failed.length };
}

// Health check
async function healthCheck() {
  const queues = ['emails', 'reports', 'data-sync'];
  const health = {};

  for (const queueName of queues) {
    const stats = await getQueueStats(queueName);
    const failed = stats.failed;
    const failureRate = stats.completed + stats.failed > 0
      ? (stats.failed / (stats.completed + stats.failed)) * 100
      : 0;

    health[queueName] = {
      ...stats,
      failureRate: failureRate.toFixed(2) + '%',
      isHealthy: failureRate < 5 && stats.waiting < 1000,
    };
  }

  return health;
}

// Emit health check endpoint
app.get('/health/queues', async (req, res) => {
  const health = await healthCheck();
  const isHealthy = Object.values(health).every(q => q.isHealthy);

  res.status(isHealthy ? 200 : 503).json(health);
});
```

### Job Progress and UI Dashboard
Track job progress:

```javascript
const progressQueue = new Queue('heavy-processing', { connection: redisClient });

// Process with progress tracking
const progressWorker = new Worker('heavy-processing', async (job) => {
  const total = 100;

  for (let i = 0; i < total; i++) {
    // Do work
    await doWork();

    // Update progress
    await job.progress((i / total) * 100);
  }

  return { result: 'completed' };
}, { connection: redisClient });

// Client-side monitoring
async function getJobProgress(jobId) {
  const queue = new Queue('heavy-processing', { connection: redisClient });
  const job = await queue.getJob(jobId);

  if (!job) return null;

  const progress = job._progress || 0;
  const state = await job.getState();

  return {
    id: job.id,
    name: job.name,
    progress,
    state,
    data: job.data,
  };
}

// WebSocket updates
io.on('connection', (socket) => {
  socket.on('watch-job', (jobId) => {
    const interval = setInterval(async () => {
      const progress = await getJobProgress(jobId);
      socket.emit('job-progress', progress);

      if (progress?.state === 'completed' || progress?.state === 'failed') {
        clearInterval(interval);
      }
    }, 1000);
  });
});
```

## Celery (Python)

### Celery Task Definition
Set up async tasks in Python:

```python
from celery import Celery, states
from celery.exceptions import SoftTimeLimitExceeded

app = Celery('myapp')
app.conf.update(
    broker_url='redis://localhost:6379',
    result_backend='redis://localhost:6379',
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

@app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    soft_time_limit=600,
)
def send_email(self, user_id, subject):
    try:
        user = User.objects.get(id=user_id)
        send_mail(
            subject,
            'message',
            'from@example.com',
            [user.email],
        )
    except Exception as exc:
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

@app.task
def generate_report(report_type):
    report = generate(report_type)
    return {'id': report.id, 'status': 'completed'}

# Schedule periodic task
from celery.schedules import crontab

app.conf.beat_schedule = {
    'daily-report': {
        'task': 'myapp.tasks.generate_report',
        'schedule': crontab(hour=2, minute=0),
        'args': ('daily',),
    },
}

# Call task
send_email.delay(user_id=123, subject='Welcome!')

# Get task status
task = send_email.apply_async((user_id, 'Welcome'))
task.state  # 'PENDING', 'STARTED', 'SUCCESS', 'FAILURE'
task.result
```

## Best Practices Summary

1. **Use Job IDs** — Prevent duplicate processing with unique job IDs
2. **Implement Retries** — Exponential backoff for transient errors
3. **Monitor Queues** — Track failed jobs and processing metrics
4. **Set Timeouts** — Prevent jobs from hanging indefinitely
5. **Log Extensively** — Include context for debugging failed jobs
6. **Test Retry Logic** — Simulate failures to verify retry behavior
7. **Clean Up Old Jobs** — Prevent database/cache bloat
8. **Distribute Work** — Use multiple workers for scaling

