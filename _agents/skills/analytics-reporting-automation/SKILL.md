---
skill_name: analytics-reporting-automation
description: Analytics automation for GA4 exports, BigQuery queries, dashboard refresh, and reporting pipelines
category: Workflow Automation
version: 1.0.0
---

# Analytics Reporting Automation

## Overview
Automated analytics keep stakeholders informed. This guide covers GA4, BigQuery, and reporting pipelines.

## Pattern 1: GA4 Daily Report

**Query GA4 → Create report → Email stakeholders**

```javascript
async function generateGA4Report() {
  const client = new BetaAnalyticsDataClient();

  // Query GA4
  const report = await client.runReport({
    property: 'properties/123456789',
    dateRanges: [
      {
        startDate: '2024-01-14',
        endDate: '2024-01-15'
      }
    ],
    dimensions: [
      { name: 'date' },
      { name: 'deviceCategory' },
      { name: 'source' }
    ],
    metrics: [
      { name: 'activeUsers' },
      { name: 'sessions' },
      { name: 'bounceRate' },
      { name: 'conversionRate' }
    ]
  });

  // Process results
  const data = {
    date: new Date().toISOString().split('T')[0],
    metrics: {
      users: 0,
      sessions: 0,
      bounceRate: 0,
      conversions: 0
    },
    byDevice: {},
    bySource: {}
  };

  for (const row of report[0].rows) {
    data.metrics.users += parseInt(row.metricValues[0].value);
    data.metrics.sessions += parseInt(row.metricValues[1].value);

    const device = row.dimensionValues[1].value;
    const source = row.dimensionValues[2].value;

    // Aggregate by device
    if (!data.byDevice[device]) {
      data.byDevice[device] = { users: 0, sessions: 0 };
    }
    data.byDevice[device].users += parseInt(row.metricValues[0].value);
    data.byDevice[device].sessions += parseInt(row.metricValues[1].value);
  }

  // Email report
  await sendReport(data, {
    recipients: ['marketing@company.com'],
    subject: `Daily Analytics Report - ${data.date}`
  });
}
```

## Pattern 2: BigQuery Scheduled Queries

**BigQuery SQL → Automated dataset update → Dashboard refresh**

```sql
-- Create scheduled query in BigQuery

CREATE OR REPLACE SCHEDULED QUERY `project.dataset.daily_metrics`
OPTIONS(
  query="""
    SELECT
      DATE(event_timestamp) as date,
      event_name,
      COUNT(*) as event_count,
      COUNT(DISTINCT user_id) as unique_users
    FROM `project.dataset.events_*`
    WHERE
      DATE(event_timestamp) = CURRENT_DATE() - 1
      AND event_name IN ('purchase', 'signup', 'login')
    GROUP BY 1, 2
  """,
  destination_dataset_id='project.analytics',
  display_name='Daily Metrics',
  frequency='DAILY',
  time_zone='America/New_York',
  query_params=['@run_time:TIMESTAMP']
)
;

-- Trigger webhook after query completes
-- (via n8n scheduled task that checks for new data)
```

## Pattern 3: Dashboard Refresh Automation

**Data updated → Looker Studio dashboard auto-refreshes**

```javascript
async function refreshDashboard() {
  // Looker Studio auto-refreshes from Google Sheets
  // So we just need to update the sheet

  const sheets = google.sheets({ version: 'v4', auth });

  // Query BigQuery for latest data
  const query = `
    SELECT date, metric, value
    FROM project.analytics.daily_summary
    WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
    ORDER BY date DESC
  `;

  const bigquery = new BigQuery();
  const [rows] = await bigquery.query({ query });

  // Update Google Sheet
  const values = [['Date', 'Metric', 'Value']];
  for (const row of rows) {
    values.push([row.date, row.metric, row.value]);
  }

  await sheets.spreadsheets.values.update({
    spreadsheetId: 'SHEET_ID',
    range: 'Analytics!A:C',
    valueInputOption: 'USER_ENTERED',
    resource: { values }
  });

  // Looker Studio reads from sheet and auto-refreshes
  console.log(`Updated ${rows.length} rows in dashboard`);
}
```

## Pattern 4: Automated Insights

**Detect anomalies and highlight in report**

```javascript
async function detectAnomalies(data) {
  const insights = [];

  // Compare to previous week
  const prevWeek = await getPreviousWeekData();

  for (const [metric, value] of Object.entries(data.metrics)) {
    const previous = prevWeek.metrics[metric];
    const change = ((value - previous) / previous) * 100;

    // Alert if > 20% change
    if (Math.abs(change) > 20) {
      insights.push({
        metric: metric,
        value: value,
        previousValue: previous,
        changePercent: change.toFixed(1),
        status: change > 0 ? 'up' : 'down',
        highlight: true
      });
    }
  }

  return insights;
}
```

## Pattern 5: Scheduled Report Delivery

**Email + Slack + Slack Dashboard**

```javascript
async function sendScheduledReports() {
  // Generate report
  const report = await generateGA4Report();
  const insights = await detectAnomalies(report);

  // Email (detailed)
  await sendEmail('exec-team@company.com', {
    subject: `Weekly Analytics Report`,
    html: renderReportHTML(report, insights),
    attachments: [
      { filename: 'report.pdf', content: renderReportPDF(report) }
    ]
  });

  // Slack (summary)
  await postToSlack('#analytics', {
    text: `📊 Weekly Metrics Summary`,
    blocks: [
      {
        type: 'section',
        fields: [
          { type: 'mrkdwn', text: `*Users:* ${report.metrics.users}` },
          { type: 'mrkdwn', text: `*Sessions:* ${report.metrics.sessions}` },
          { type: 'mrkdwn', text: `*Conversion:* ${report.metrics.conversions}%` }
        ]
      },
      {
        type: 'section',
        text: {
          type: 'mrkdwn',
          text: `*Key Changes:*\n${insights.map(i =>
            `${i.status === 'up' ? '📈' : '📉'} ${i.metric}: ${i.changePercent}%`
          ).join('\n')}`
        }
      }
    ]
  });

  // Update Slack status (optional)
  await updateSlackStatus({
    status_emoji: ':chart_with_upwards_trend:',
    status_text: `Daily users: ${report.metrics.users}`
  });
}
```

## Best Practices

1. **Query efficiently** — Use sampling/filters
2. **Cache results** — Don't requery same data
3. **Schedule off-peak** — Night/early morning
4. **Automate delivery** — Don't manually send
5. **Highlight anomalies** — Easy to spot issues
6. **Compare to baseline** — Week/month over month
7. **Track KPIs** — Consistent metrics
8. **Version reports** — Archive for history
9. **Segment data** — By device, source, etc.
10. **Visualize clearly** — Charts > numbers

