---
skill_name: audit-log-patterns
description: Audit logging design with event sourcing, what to log, retention policies, querying, and compliance requirements
category: Backend Development
version: 1.0.0
---

# Audit Log Patterns

Master audit logging for compliance, debugging, and forensic analysis.

## Audit Log Schema

```javascript
// MongoDB schema
db.createCollection('auditLogs', {
    validator: {
        $jsonSchema: {
            bsonType: 'object',
            required: ['event', 'userId', 'resourceType', 'resourceId', 'timestamp', 'changes'],
            properties: {
                _id: { bsonType: 'objectId' },
                event: { enum: ['CREATE', 'UPDATE', 'DELETE', 'READ', 'LOGIN', 'LOGOUT', 'PERMISSION_CHANGE'] },
                userId: { bsonType: 'string' },
                userEmail: { bsonType: 'string' },
                resourceType: { bsonType: 'string' }, // 'user', 'order', 'invoice', etc
                resourceId: { bsonType: 'string' },
                resourceName: { bsonType: 'string' }, // User-friendly name
                action: { bsonType: 'string' }, // Detailed action description
                changes: {
                    bsonType: 'object',
                    properties: {
                        before: { bsonType: 'object' }, // Previous state
                        after: { bsonType: 'object' },  // New state
                    },
                },
                ipAddress: { bsonType: 'string' },
                userAgent: { bsonType: 'string' },
                status: { enum: ['SUCCESS', 'FAILED'] },
                errorMessage: { bsonType: 'string' },
                timestamp: { bsonType: 'date' },
                severity: { enum: ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'] },
                metadata: { bsonType: 'object' }, // Additional context
            },
        },
    },
});

// Create indexes for performance
db.auditLogs.createIndex({ userId: 1, timestamp: -1 });
db.auditLogs.createIndex({ resourceType: 1, resourceId: 1, timestamp: -1 });
db.auditLogs.createIndex({ timestamp: -1 });
db.auditLogs.createIndex({ event: 1, timestamp: -1 });
db.auditLogs.createIndex({ severity: 1, timestamp: -1 });
```

## Core Audit Logger

```javascript
class AuditLogger {
    constructor(db, redisClient) {
        this.db = db;
        this.redis = redisClient;
    }

    async log(auditEntry) {
        const enrichedEntry = {
            ...auditEntry,
            timestamp: new Date(),
            _id: new ObjectId(),
        };

        // Validate sensitive data isn't logged raw
        this.validateSensitiveData(enrichedEntry);

        // Store in database
        await this.db.collection('auditLogs').insertOne(enrichedEntry);

        // Cache for real-time queries
        await this.redis.zadd(
            `audit:recent:${auditEntry.resourceType}`,
            Date.now(),
            JSON.stringify(enrichedEntry),
            'EX',
            3600 // 1 hour cache
        );

        // Index for quick access
        if (auditEntry.severity === 'CRITICAL') {
            await this.redis.lpush('audit:critical', JSON.stringify(enrichedEntry));
            await this.redis.ltrim('audit:critical', 0, 999); // Keep last 1000
        }

        return enrichedEntry._id;
    }

    validateSensitiveData(entry) {
        const sensitiveFields = ['password', 'apiKey', 'token', 'ssn', 'creditCard'];

        for (const field of sensitiveFields) {
            if (entry.changes?.before?.[field]) {
                entry.changes.before[field] = '***REDACTED***';
            }
            if (entry.changes?.after?.[field]) {
                entry.changes.after[field] = '***REDACTED***';
            }
        }
    }

    async getLog(auditId) {
        return this.db.collection('auditLogs').findOne({ _id: new ObjectId(auditId) });
    }

    async getUserAuditTrail(userId, limit = 100, offset = 0) {
        return this.db.collection('auditLogs')
            .find({ userId })
            .sort({ timestamp: -1 })
            .skip(offset)
            .limit(limit)
            .toArray();
    }

    async getResourceHistory(resourceType, resourceId) {
        return this.db.collection('auditLogs')
            .find({ resourceType, resourceId })
            .sort({ timestamp: -1 })
            .toArray();
    }
}
```

## Integration with Application

```javascript
// Middleware to capture audit context
app.use((req, res, next) => {
    req.auditContext = {
        userId: req.user?.id || 'ANONYMOUS',
        userEmail: req.user?.email,
        ipAddress: req.ip,
        userAgent: req.get('user-agent'),
        timestamp: new Date(),
    };
    next();
});

// Example: Log user creation
async function createUser(req, res) {
    const newUser = {
        email: req.body.email,
        name: req.body.name,
        role: req.body.role || 'user',
    };

    const savedUser = await db.user.create(newUser);

    // Audit log
    await auditLogger.log({
        ...req.auditContext,
        event: 'CREATE',
        resourceType: 'user',
        resourceId: savedUser.id,
        resourceName: savedUser.email,
        action: `Created user ${savedUser.email} with role ${newUser.role}`,
        changes: {
            before: null,
            after: newUser,
        },
        status: 'SUCCESS',
        severity: 'MEDIUM',
    });

    res.json(savedUser);
}

// Example: Log user update
async function updateUser(req, res) {
    const userId = req.params.id;
    const oldUser = await db.user.findById(userId);
    const updates = req.body;

    const updatedUser = await db.user.update(userId, updates);

    // Log changes only
    const changes = {};
    for (const [key, value] of Object.entries(updates)) {
        if (oldUser[key] !== value) {
            changes[key] = { before: oldUser[key], after: value };
        }
    }

    await auditLogger.log({
        ...req.auditContext,
        event: 'UPDATE',
        resourceType: 'user',
        resourceId: userId,
        resourceName: oldUser.email,
        action: `Updated user ${oldUser.email}: ${Object.keys(changes).join(', ')}`,
        changes: {
            before: { ...oldUser },
            after: { ...oldUser, ...updates },
        },
        status: 'SUCCESS',
        severity: detectSeverity(changes),
    });

    res.json(updatedUser);
}

function detectSeverity(changes) {
    const criticalFields = ['role', 'permissions', 'email', 'mfaEnabled'];
    const criticalChanges = Object.keys(changes).some(k => criticalFields.includes(k));
    return criticalChanges ? 'HIGH' : 'MEDIUM';
}
```

## Retention and Archival

```javascript
class AuditLogRetention {
    constructor(db, s3Client) {
        this.db = db;
        this.s3 = s3Client;
    }

    async archiveOldLogs() {
        // Archive logs older than 1 year
        const archiveDate = new Date();
        archiveDate.setFullYear(archiveDate.getFullYear() - 1);

        // Read logs to archive
        const logsToArchive = await this.db.collection('auditLogs')
            .find({ timestamp: { $lt: archiveDate } })
            .toArray();

        if (logsToArchive.length === 0) return;

        // Archive to S3
        const archiveKey = `audit-logs/${archiveDate.getFullYear()}-${String(archiveDate.getMonth() + 1).padStart(2, '0')}.json.gz`;
        const gzipData = gzip(JSON.stringify(logsToArchive));

        await this.s3.putObject({
            Bucket: 'audit-archive',
            Key: archiveKey,
            Body: gzipData,
            ContentType: 'application/json+gzip',
            Metadata: {
                'archive-date': archiveDate.toISOString(),
                'log-count': logsToArchive.length.toString(),
            },
        }).promise();

        // Delete archived logs
        await this.db.collection('auditLogs').deleteMany({
            timestamp: { $lt: archiveDate },
        });

        // Log the archival itself
        console.log(`Archived ${logsToArchive.length} logs to ${archiveKey}`);
    }

    async deleteExpiredLogs() {
        // Delete logs older than retention period (default 7 years)
        const deleteDate = new Date();
        deleteDate.setFullYear(deleteDate.getFullYear() - 7);

        const result = await this.db.collection('auditLogs').deleteMany({
            timestamp: { $lt: deleteDate },
        });

        console.log(`Deleted ${result.deletedCount} expired logs`);
    }

    async setupRetentionPolicy() {
        // TTL index to auto-delete logs after 7 years
        await this.db.collection('auditLogs').createIndex(
            { timestamp: 1 },
            { expireAfterSeconds: 7 * 365 * 24 * 60 * 60 }
        );
    }
}
```

## Querying and Reporting

```javascript
class AuditQueryBuilder {
    constructor(db) {
        this.db = db;
    }

    async findSuspiciousActivity(timeWindowHours = 24) {
        const since = new Date(Date.now() - timeWindowHours * 60 * 60 * 1000);

        // Failed login attempts
        const failedLogins = await this.db.collection('auditLogs')
            .aggregate([
                {
                    $match: {
                        event: 'LOGIN',
                        status: 'FAILED',
                        timestamp: { $gte: since },
                    },
                },
                {
                    $group: {
                        _id: '$userId',
                        count: { $sum: 1 },
                        lastAttempt: { $max: '$timestamp' },
                    },
                },
                { $match: { count: { $gte: 5 } } }, // 5+ failed attempts
            ])
            .toArray();

        return {
            timeWindow: `${timeWindowHours} hours`,
            suspiciousUsers: failedLogins,
        };
    }

    async auditTrailForResource(resourceType, resourceId) {
        const logs = await this.db.collection('auditLogs')
            .find({
                resourceType,
                resourceId,
            })
            .sort({ timestamp: -1 })
            .toArray();

        // Reconstruct state at each point in time
        const timeline = [];
        let state = null;

        for (let i = logs.length - 1; i >= 0; i--) {
            const log = logs[i];
            state = log.changes?.after || {};

            timeline.push({
                timestamp: log.timestamp,
                event: log.event,
                actor: log.userEmail,
                state,
            });
        }

        return timeline;
    }

    async complianceReport(fromDate, toDate, resourceType) {
        return this.db.collection('auditLogs')
            .aggregate([
                {
                    $match: {
                        timestamp: { $gte: fromDate, $lte: toDate },
                        resourceType,
                    },
                },
                {
                    $group: {
                        _id: { event: '$event', userId: '$userId' },
                        count: { $sum: 1 },
                    },
                },
                {
                    $sort: { count: -1 },
                },
            ])
            .toArray();
    }
}
```

## Compliance and Security

```javascript
class ComplianceAuditor {
    async generateSOC2Report(month, year) {
        const startDate = new Date(year, month - 1, 1);
        const endDate = new Date(year, month, 0, 23, 59, 59);

        return {
            period: `${month}/${year}`,
            criticalEvents: await this.getCriticalEvents(startDate, endDate),
            accessPatterns: await this.analyzeAccessPatterns(startDate, endDate),
            dataChanges: await this.getDataChangesSummary(startDate, endDate),
            unusualActivity: await this.detectUnusualActivity(startDate, endDate),
        };
    }

    async getCriticalEvents(from, to) {
        return this.db.collection('auditLogs')
            .find({
                severity: 'CRITICAL',
                timestamp: { $gte: from, $lte: to },
            })
            .toArray();
    }

    async analyzeAccessPatterns(from, to) {
        return this.db.collection('auditLogs')
            .aggregate([
                {
                    $match: {
                        event: 'READ',
                        timestamp: { $gte: from, $lte: to },
                    },
                },
                {
                    $group: {
                        _id: { userId: '$userId', resourceType: '$resourceType' },
                        accessCount: { $sum: 1 },
                    },
                },
            ])
            .toArray();
    }
}
```

## Best Practices

- Log the who, what, when, where, why, and how for every action
- Never log sensitive data (passwords, API keys)
- Use structured logging for easy querying
- Implement retention policies based on regulations (GDPR, HIPAA, SOC2)
- Archive logs after active period expires
- Create indexes on frequently queried fields
- Monitor for suspicious patterns automatically
- Ensure audit logs themselves are immutable
- Use consistent timestamps (UTC)
- Log failed actions with reasons
