---
skill_name: background-job-patterns
description: Background job design with BullMQ, Sidekiq patterns including retry strategies, job queuing, and monitoring
category: Backend Development
version: 1.0.0
---

# Background Job Patterns

Master asynchronous job processing with proper retry logic, error handling, and observability.

## BullMQ Setup (Node.js)

```javascript
import { Queue, Worker, QueueScheduler } from 'bullmq';
import Redis from 'ioredis';

const connection = new Redis({
    host: 'localhost',
    port: 6379,
    maxRetriesPerRequest: null,
    enableReadyCheck: false,
});

// Create queue
const emailQueue = new Queue('send-email', { connection });
const imageQueue = new Queue('process-image', { connection });

// Add job
const job = await emailQueue.add(
    'welcome-email',
    {
        userId: '123',
        email: 'user@example.com',
    },
    {
        delay: 5000, // Run in 5 seconds
        attempts: 3,
        backoff: {
            type: 'exponential',
            delay: 2000,
        },
        removeOnComplete: true,
        removeOnFail: false,
    }
);

console.log(`Job added with ID: ${job.id}`);
```

## Worker Implementation

```javascript
// Basic worker
const emailWorker = new Worker(
    'send-email',
    async (job) => {
        console.log(`Processing job ${job.id}`);

        const { email, userId } = job.data;

        // Send email
        await sendEmail(email, 'Welcome!', 'Welcome template');

        // Update user
        await db.user.update(
            { id: userId },
            { emailVerified: true }
        );

        return { success: true, email };
    },
    { connection, concurrency: 5 }
);

emailWorker.on('completed', (job, result) => {
    console.log(`Job ${job.id} completed: ${JSON.stringify(result)}`);
});

emailWorker.on('failed', (job, err) => {
    console.error(`Job ${job.id} failed: ${err.message}`);
});

emailWorker.on('error', (err) => {
    console.error('Worker error:', err);
});

// Worker with graceful shutdown
process.on('SIGTERM', async () => {
    await emailWorker.close();
    process.exit(0);
});
```

## Retry Strategies

```javascript
// Exponential backoff
const job1 = await queue.add('task', data, {
    attempts: 5,
    backoff: {
        type: 'exponential',
        delay: 2000, // 2s, 4s, 8s, 16s, 32s
    },
});

// Fixed delay
const job2 = await queue.add('task', data, {
    attempts: 3,
    backoff: {
        type: 'fixed',
        delay: 5000, // Always 5s between retries
    },
});

// Custom retry logic
const worker = new Worker('task', async (job) => {
    const maxAttempts = 3;
    const attempt = job.attemptsMade + 1;

    try {
        return await processWithRetry(job.data, attempt);
    } catch (error) {
        if (attempt < maxAttempts && isRetryable(error)) {
            throw error; // Will be retried
        } else {
            // Store error for later analysis
            await logFailedJob(job.id, error);
            throw new Error(`Job failed after ${maxAttempts} attempts`);
        }
    }
}, { connection });

function isRetryable(error) {
    // Retry on network errors, not on validation errors
    return error.code === 'ECONNREFUSED' ||
           error.code === 'ETIMEDOUT' ||
           error.code === 'EHOSTUNREACH';
}
```

## Job Prioritization

```javascript
// Create priority queues
const criticalQueue = new Queue('notifications', {
    connection,
    defaultJobOptions: {
        priority: 1, // Highest priority
    },
});

const normalQueue = new Queue('notifications', {
    connection,
    defaultJobOptions: {
        priority: 5, // Normal priority
    },
});

const lowPriorityQueue = new Queue('notifications', {
    connection,
    defaultJobOptions: {
        priority: 10, // Lowest priority
    },
});

// Add jobs with different priorities
await criticalQueue.add('alert', { message: 'Critical alert' });
await normalQueue.add('reminder', { message: 'Reminder' });
await lowPriorityQueue.add('newsletter', { message: 'Newsletter' });

// Worker processes jobs by priority
const worker = new Worker(
    'notifications',
    async (job) => {
        console.log(`Processing ${job.name} with priority ${job.opts.priority}`);
        // Process job
    },
    {
        connection,
        concurrency: 10,
        // Process higher priority jobs first
        settings: {
            lockDuration: 30000,
            lockRenewTime: 15000,
        },
    }
);
```

## Job Scheduling

```javascript
// Schedule job to run at specific time
const job = await queue.add(
    'send-report',
    { reportId: '123' },
    {
        repeat: {
            pattern: '0 9 * * *', // Every day at 9 AM
        },
        removeOnComplete: true,
    }
);

// Repeat job N times
const job2 = await queue.add(
    'cleanup',
    { folder: '/tmp' },
    {
        repeat: {
            limit: 10, // Run 10 times
            every: 3600000, // Every hour
        },
    }
);

// Complex schedule
const job3 = await queue.add(
    'sync-data',
    { dataSource: 'api' },
    {
        repeat: {
            pattern: '0 */6 * * *', // Every 6 hours
            tz: 'America/New_York',
        },
    }
);

// QueueScheduler manages repeated jobs
const scheduler = new QueueScheduler('send-report', { connection });
scheduler.on('error', (err) => {
    console.error('Scheduler error:', err);
});
```

## Job Status Tracking

```javascript
// Check job status
const job = await queue.getJob('job-id');
console.log(job.progress());
console.log(job.data);
console.log(job.attemptsMade);
console.log(job.finishedOn);
console.log(job.failedReason);

// List jobs by status
const active = await queue.getActive();
const waiting = await queue.getWaiting();
const completed = await queue.getCompleted();
const failed = await queue.getFailed();

console.log(`Active: ${active.length}, Waiting: ${waiting.length}`);
console.log(`Completed: ${completed.length}, Failed: ${failed.length}`);

// Monitor job progress
const worker = new Worker('heavy-task', async (job) => {
    const totalItems = 1000;

    for (let i = 0; i < totalItems; i++) {
        await processItem(i);
        // Report progress
        await job.updateProgress((i / totalItems) * 100);
    }

    return { processed: totalItems };
}, { connection });

// Client watches progress
const job = await queue.add('heavy-task', {});
job.on('progress', (progress) => {
    console.log(`Progress: ${progress}%`);
});
```

## Error Handling and DLQ

```javascript
// Catch errors and move to DLQ after max retries
const worker = new Worker('process-data', async (job) => {
    try {
        return await processData(job.data);
    } catch (error) {
        console.error(`Job ${job.id} error:`, error);
        throw error;
    }
}, { connection });

worker.on('failed', async (job, err) => {
    console.log(`Job ${job.id} failed: ${err.message}`);

    if (job.attemptsMade >= job.opts.attempts) {
        // Move to DLQ
        await dlqQueue.add('failed-job', {
            originalJobId: job.id,
            originalData: job.data,
            error: err.message,
            timestamp: new Date(),
            attempts: job.opts.attempts,
        });
    }
});

// Process DLQ jobs
const dlqWorker = new Worker('failed-job', async (job) => {
    // Send alert
    await sendAlert(`Job ${job.data.originalJobId} permanently failed`);

    // Store in database for manual review
    await failedJobsDb.insert({
        jobId: job.data.originalJobId,
        data: job.data.originalData,
        error: job.data.error,
        timestamp: job.data.timestamp,
    });
}, { connection });
```

## Monitoring and Metrics

```javascript
// Queue statistics
async function getQueueStats() {
    const stats = {
        waiting: await queue.getWaitingCount(),
        active: await queue.getActiveCount(),
        completed: await queue.getCompletedCount(),
        failed: await queue.getFailedCount(),
        paused: await queue.getPausedCount(),
    };

    return stats;
}

// Worker health check
const worker = new Worker('task', processor, { connection });

let lastHeartbeat = Date.now();
worker.on('active', () => {
    lastHeartbeat = Date.now();
});

setInterval(() => {
    const downtime = Date.now() - lastHeartbeat;
    if (downtime > 60000) {
        console.warn('Worker heartbeat timeout');
        // Alert monitoring system
    }
}, 30000);

// Prometheus metrics
import promClient from 'prom-client';

const jobsQueue = new promClient.Counter({
    name: 'bullmq_jobs_total',
    help: 'Total jobs processed',
    labelNames: ['queue', 'status'],
});

worker.on('completed', (job) => {
    jobsQueue.inc({ queue: 'task', status: 'success' });
});

worker.on('failed', (job) => {
    jobsQueue.inc({ queue: 'task', status: 'failed' });
});
```

## Sidekiq (Ruby) Pattern

```ruby
# app/jobs/send_email_job.rb
class SendEmailJob
  include Sidekiq::Job
  sidekiq_options retry: 5, queue: 'default'

  def perform(user_id)
    user = User.find(user_id)
    UserMailer.welcome_email(user).deliver_later
  rescue StandardError => e
    logger.error("Failed to send email to user #{user_id}: #{e.message}")
    raise e if sidekiq_retries_exhausted?
  end

  sidekiq_retry_in { 2 ** (sidekiq_retries_exhausted? ? 10 : @retry_count) }
  sidekiq_dead do |msg, exception|
    Airbrake.notify(exception, job: msg)
  end
end

# Usage
SendEmailJob.perform_async(user_id)
SendEmailJob.set(wait_until: Date.tomorrow.noon).perform_async(user_id)
```

## Best Practices

- Set reasonable TTL on jobs to prevent infinite queuing
- Use idempotency keys for jobs that may be processed twice
- Implement circuit breakers for external service calls
- Monitor queue depth and worker saturation
- Use dead-letter queues for permanent failures
- Set timeouts on job processing
- Batch related jobs for efficiency
- Use priority queues sparingly
