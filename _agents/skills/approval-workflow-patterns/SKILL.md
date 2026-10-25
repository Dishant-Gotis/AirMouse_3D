---
skill_name: approval-workflow-patterns
description: Approval workflow patterns for multi-level approvals, SLA tracking, reminders, and audit trails
category: Workflow Automation
version: 1.0.0
---

# Approval Workflow Patterns

## Overview
Multi-stage approval workflows ensure proper oversight. This guide covers routing, SLAs, and audit trails.

## Pattern 1: Expense Approval Workflow

**Expense submitted → Manager → Finance → Paid**

```javascript
async function expenseApprovalWorkflow(expense) {
  // Level 1: Manager approval
  const managerApproval = await createApprovalRequest({
    entityId: expense.id,
    type: 'expense',
    level: 1,
    approver: expense.submitterManager,
    deadline: addDays(new Date(), 3),
    data: expense
  });

  // Send email
  await sendApprovalRequest(expense.submitterManager, {
    message: `Expense approval needed: $${expense.amount}`,
    expense: expense,
    approveUrl: managerApproval.approveUrl,
    rejectUrl: managerApproval.rejectUrl
  });

  // Wait for approval
  const managerResult = await waitForApproval(managerApproval.id);

  if (!managerResult.approved) {
    return { status: 'rejected', level: 1, reason: managerResult.reason };
  }

  // Level 2: Finance review (if > $5000)
  if (expense.amount > 5000) {
    const financeApproval = await createApprovalRequest({
      entityId: expense.id,
      type: 'expense',
      level: 2,
      approver: 'finance-team@company.com',
      deadline: addDays(new Date(), 2)
    });

    const financeResult = await waitForApproval(financeApproval.id);

    if (!financeResult.approved) {
      return { status: 'rejected', level: 2, reason: financeResult.reason };
    }
  }

  // Approved: Process payment
  await processPayment(expense);

  return { status: 'approved', paidDate: new Date() };
}
```

## Pattern 2: SLA Tracking

**Track approval time against SLAs**

```javascript
async function trackApprovalSLA(approval) {
  const sla = getApprovalSLA(approval.type, approval.amount);

  // sla = { responseTime: 24h, escalationLevel: 'manager' }

  const elapsed = Date.now() - approval.createdAt;

  if (elapsed > sla.responseTime) {
    // SLA breached: escalate
    await escalateApproval(approval, sla.escalationLevel);

    await alertOps({
      message: `Approval SLA breached: ${approval.type}`,
      duration: elapsed / (1000 * 60 * 60),
      sla: sla.responseTime / (1000 * 60 * 60)
    });
  }

  // Track in analytics
  await logApprovalMetric({
    type: approval.type,
    duration: elapsed,
    slaTarget: sla.responseTime,
    metuSLA: elapsed <= sla.responseTime
  });
}
```

## Pattern 3: Reminder Automation

**No response → Auto-send reminders**

```javascript
async function sendApprovalReminders() {
  const pending = await getPendingApprovals();

  for (const approval of pending) {
    const hoursPending = (Date.now() - approval.createdAt) / (1000 * 60 * 60);

    // First reminder: 24 hours
    if (hoursPending === 24 && !approval.reminder1Sent) {
      await sendEmail(approval.approver, {
        subject: `⏰ Reminder: Approval needed for ${approval.type}`,
        body: `You have a pending ${approval.type} approval.`,
        actionUrl: approval.approveUrl
      });

      await markReminderSent(approval.id, 1);
    }

    // Second reminder: 48 hours + escalation
    if (hoursPending === 48 && !approval.reminder2Sent) {
      await sendEmail(approval.approver, {
        subject: `⚠️  URGENT: Approval overdue for ${approval.type}`,
        body: 'This approval is now overdue. Manager will be notified.'
      });

      // Escalate to manager
      await sendEmail(approval.approverManager, {
        subject: `Escalation: ${approval.approver} has overdue approval`,
        body: `${approval.approver} has not approved this ${approval.type} within SLA`
      });

      await markReminderSent(approval.id, 2);
    }
  }
}
```

## Pattern 4: Parallel Approvals

**Multiple approvers needed simultaneously**

```javascript
async function parallelApprovalWorkflow(request) {
  // All signatories must approve
  const approvers = await getApproversForRequest(request);

  const approvalRequests = approvers.map(approver =>
    createApprovalRequest({
      entityId: request.id,
      approver: approver.email,
      deadline: addDays(new Date(), 2),
      parallel: true
    })
  );

  const approvalIds = approvalRequests.map(a => a.id);

  // Wait for ALL to approve (or timeout)
  const results = await Promise.allSettled(
    approvalIds.map(id => waitForApproval(id))
  );

  const approved = results.filter(r => r.status === 'fulfilled' && r.value.approved);
  const rejected = results.filter(r => r.status === 'rejected' || !r.value.approved);

  if (rejected.length > 0) {
    return {
      status: 'rejected',
      rejectedBy: rejected.map(r => r.approver)
    };
  }

  return { status: 'approved', approvedBy: approved.map(a => a.approver) };
}
```

## Pattern 5: Audit Trail

**Log all approval decisions**

```javascript
async function logApprovalDecision(approval, decision) {
  const auditLog = {
    approvalId: approval.id,
    entityId: approval.entityId,
    entityType: approval.type,
    approver: approval.approver,
    decision: decision.action, // 'approved', 'rejected', 'delegated'
    timestamp: new Date(),
    comments: decision.comments,
    ipAddress: getClientIP(),
    userAgent: getUserAgent()
  };

  // Store
  await saveAuditLog(auditLog);

  // If rejected: capture reason
  if (decision.action === 'rejected') {
    await updateEntity(approval.entityId, {
      rejectionReason: decision.comments,
      rejectedAt: new Date(),
      rejectedBy: approval.approver
    });
  }

  // If approved: move to next step
  if (decision.action === 'approved') {
    const workflow = getWorkflowForEntity(approval.type);
    const nextStep = workflow.getNextStep(approval.level);

    if (nextStep) {
      await createApprovalRequest({
        ...approval,
        level: nextStep.level,
        approver: nextStep.approver
      });
    } else {
      // Workflow complete
      await finalizeEntity(approval.entityId);
    }
  }
}
```

## Best Practices

1. **Set clear SLAs** — Define response times
2. **Auto-escalate** — Don't let approvals stall
3. **Provide context** — Show full entity details
4. **Enable delegation** — Approver is out? Delegate to colleague
5. **Audit everything** — Track who approved what
6. **Send reminders** — Push notifications, not pull
7. **Make approving easy** — One-click approve/reject
8. **Log reasons** — Why was it rejected?
9. **Prevent bottlenecks** — Monitor cycle times
10. **Mobile-friendly** — Approvers are often mobile

