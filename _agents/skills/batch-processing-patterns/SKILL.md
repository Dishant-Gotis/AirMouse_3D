---
skill_name: batch-processing-patterns
description: Batch processing - chunking, checkpointing, parallel workers, resumability, state management
category: [backend, advanced]
version: 1.0.0
---

# Batch Processing Patterns

## Basic Batch Processing

```typescript
async function processBatch(items: Item[]): Promise<void> {
  const batchSize = 100;

  for (let i = 0; i < items.length; i += batchSize) {
    const batch = items.slice(i, i + batchSize);
    await processBatchChunk(batch);
  }
}

async function processBatchChunk(batch: Item[]): Promise<void> {
  const promises = batch.map(item => processItem(item));
  await Promise.all(promises);
}

async function processItem(item: Item): Promise<void> {
  try {
    await saveToDatabase(item);
    await sendNotification(item);
  } catch (error) {
    console.error(`Failed to process item ${item.id}:`, error);
    throw error;
  }
}
```

## Checkpointing for Resumability

```typescript
interface CheckpointData {
  processedCount: number;
  totalCount: number;
  lastProcessedId: string;
  status: 'in-progress' | 'completed' | 'failed';
  timestamp: number;
}

class BatchProcessor {
  private checkpointFile: string;
  private checkpoint: CheckpointData;

  constructor(checkpointFile: string) {
    this.checkpointFile = checkpointFile;
    this.loadCheckpoint();
  }

  private loadCheckpoint(): void {
    try {
      const data = fs.readFileSync(this.checkpointFile, 'utf-8');
      this.checkpoint = JSON.parse(data);
    } catch {
      this.checkpoint = {
        processedCount: 0,
        totalCount: 0,
        lastProcessedId: '',
        status: 'in-progress',
        timestamp: Date.now()
      };
    }
  }

  private saveCheckpoint(): void {
    fs.writeFileSync(
      this.checkpointFile,
      JSON.stringify(this.checkpoint, null, 2)
    );
  }

  async process(items: Item[]): Promise<void> {
    this.checkpoint.totalCount = items.length;

    // Find resume point
    let startIndex = 0;
    if (this.checkpoint.lastProcessedId) {
      startIndex = items.findIndex(
        i => i.id === this.checkpoint.lastProcessedId
      ) + 1;
    }

    const batchSize = 100;

    for (let i = startIndex; i < items.length; i += batchSize) {
      const batch = items.slice(i, i + batchSize);

      try {
        await this.processBatch(batch);
        this.checkpoint.processedCount = i + batch.length;
        this.checkpoint.lastProcessedId = batch[batch.length - 1].id;
        this.saveCheckpoint();
      } catch (error) {
        console.error('Batch failed:', error);
        this.checkpoint.status = 'failed';
        this.saveCheckpoint();
        throw error;
      }
    }

    this.checkpoint.status = 'completed';
    this.saveCheckpoint();
  }

  private async processBatch(batch: Item[]): Promise<void> {
    await Promise.all(batch.map(item => this.processItem(item)));
  }

  private async processItem(item: Item): Promise<void> {
    // Process logic
  }

  getProgress(): number {
    return (this.checkpoint.processedCount / this.checkpoint.totalCount) * 100;
  }
}
```

## Parallel Workers with Queue

```typescript
class BatchWorkerPool {
  private queue: Item[] = [];
  private workers: Promise<void>[] = [];
  private activeWorkers = 0;

  constructor(private concurrency: number) {}

  async addItems(items: Item[]): Promise<void> {
    this.queue.push(...items);
  }

  async process(): Promise<void> {
    // Start workers
    for (let i = 0; i < this.concurrency; i++) {
      this.workers.push(this.worker());
    }

    await Promise.all(this.workers);
  }

  private async worker(): Promise<void> {
    while (this.queue.length > 0) {
      const item = this.queue.shift();
      if (!item) break;

      this.activeWorkers++;
      try {
        await this.processItem(item);
      } catch (error) {
        console.error(`Worker failed on ${item.id}:`, error);
        // Re-queue failed items
        this.queue.push(item);
      } finally {
        this.activeWorkers--;
      }
    }
  }

  private async processItem(item: Item): Promise<void> {
    // Processing logic
  }

  getStats(): {
    queued: number;
    activeWorkers: number;
    totalProcessed: number;
  } {
    return {
      queued: this.queue.length,
      activeWorkers: this.activeWorkers,
      totalProcessed: 0 // Track separately
    };
  }
}
```

## Error Handling & Retries

```typescript
interface BatchResult {
  successful: Item[];
  failed: Array<{ item: Item; error: string }>;
  retryable: Array<{ item: Item; error: string }>;
}

class RobustBatchProcessor {
  async processBatch(
    items: Item[],
    options = { maxRetries: 3, retryDelay: 1000 }
  ): Promise<BatchResult> {
    const result: BatchResult = {
      successful: [],
      failed: [],
      retryable: []
    };

    let currentItems = items;
    let retryCount = 0;

    while (currentItems.length > 0 && retryCount < options.maxRetries) {
      const processed = await Promise.allSettled(
        currentItems.map(item => this.processItem(item))
      );

      currentItems = [];

      for (let i = 0; i < processed.length; i++) {
        const outcome = processed[i];
        const item = currentItems[i];

        if (outcome.status === 'fulfilled') {
          result.successful.push(item);
        } else {
          const error = outcome.reason as Error;

          if (this.isRetryable(error)) {
            currentItems.push(item);
          } else {
            result.failed.push({ item, error: error.message });
          }
        }
      }

      if (currentItems.length > 0) {
        retryCount++;
        await this.delay(options.retryDelay * Math.pow(2, retryCount - 1));
      }
    }

    // Remaining items after max retries
    result.retryable = currentItems.map(item => ({
      item,
      error: 'Max retries exceeded'
    }));

    return result;
  }

  private isRetryable(error: Error): boolean {
    const retryableErrors = ['TIMEOUT', 'RATE_LIMIT', 'ECONNREFUSED'];
    return retryableErrors.some(msg => error.message.includes(msg));
  }

  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  private async processItem(item: Item): Promise<void> {
    // Implementation
  }
}
```

## Progress Tracking

```typescript
class ProgressTracker {
  private processed = 0;
  private failed = 0;
  private total = 0;
  private startTime = Date.now();

  constructor(total: number) {
    this.total = total;
  }

  recordSuccess(): void {
    this.processed++;
  }

  recordFailure(): void {
    this.failed++;
  }

  getProgress(): {
    processed: number;
    failed: number;
    remaining: number;
    percentage: number;
    itemsPerSecond: number;
    estimatedTimeRemaining: number;
  } {
    const completed = this.processed + this.failed;
    const elapsedSeconds = (Date.now() - this.startTime) / 1000;
    const itemsPerSecond = completed / elapsedSeconds;

    return {
      processed: this.processed,
      failed: this.failed,
      remaining: this.total - completed,
      percentage: Math.round((completed / this.total) * 100),
      itemsPerSecond: Math.round(itemsPerSecond),
      estimatedTimeRemaining: Math.round(
        (this.total - completed) / itemsPerSecond
      )
    };
  }

  printProgress(): void {
    const p = this.getProgress();
    console.log(
      `Progress: ${p.processed}/${this.total} (${p.percentage}%) | ` +
      `Speed: ${p.itemsPerSecond}/s | ` +
      `ETA: ${p.estimatedTimeRemaining}s`
    );
  }
}

// Usage
const tracker = new ProgressTracker(10000);

for (let i = 0; i < 10000; i++) {
  try {
    await processItem(items[i]);
    tracker.recordSuccess();
  } catch (error) {
    tracker.recordFailure();
  }

  if ((i + 1) % 100 === 0) {
    tracker.printProgress();
  }
}
```

## Streaming Large Files

```typescript
import { createReadStream } from 'fs';
import { createInterface } from 'readline';

async function processLargeFile(filePath: string): Promise<void> {
  const readStream = createReadStream(filePath);
  const rl = createInterface({
    input: readStream,
    crlfDelay: Infinity
  });

  let batch: string[] = [];
  const batchSize = 1000;

  for await (const line of rl) {
    batch.push(line);

    if (batch.length >= batchSize) {
      await processBatch(batch);
      batch = [];
    }
  }

  // Process remaining items
  if (batch.length > 0) {
    await processBatch(batch);
  }
}

async function processBatch(items: string[]): Promise<void> {
  const promises = items.map(item => processItem(item));
  await Promise.all(promises);
}
```

## Dead Letter Queue

```typescript
class BatchProcessorWithDLQ {
  private deadLetterQueue: Item[] = [];

  async processBatch(items: Item[]): Promise<void> {
    for (const item of items) {
      try {
        await this.processItem(item);
      } catch (error) {
        if (this.isRetryable(error)) {
          throw error; // Re-throw for retry logic
        } else {
          // Send to DLQ for manual inspection
          this.deadLetterQueue.push(item);
          await this.logToDLQ(item, error);
        }
      }
    }
  }

  private async logToDLQ(item: Item, error: Error): Promise<void> {
    const dlqEntry = {
      item,
      error: error.message,
      timestamp: new Date(),
      stack: error.stack
    };

    // Write to file/database
    fs.appendFileSync(
      'dead-letter-queue.jsonl',
      JSON.stringify(dlqEntry) + '\n'
    );
  }

  private isRetryable(error: Error): boolean {
    return error.message.includes('TIMEOUT') ||
           error.message.includes('RATE_LIMIT');
  }

  private async processItem(item: Item): Promise<void> {
    // Processing
  }
}
```

## Key Takeaways

- **Chunking**: Process in batches to manage memory
- **Checkpointing**: Save progress to enable resumption
- **Parallel workers**: Use concurrency limits to prevent overload
- **Error classification**: Distinguish retriable vs permanent errors
- **Progress tracking**: Monitor speed and estimate completion
- **DLQ**: Route problematic items for manual inspection
