---
skill_name: airtable-automation-guide
description: >
  Master Airtable base design, automations, interfaces, scripts, and integrations.
  Cover automation triggers/actions, scripting APIs, field types, view hierarchies,
  and enterprise deployment. Use when building data workflows, automations, or scalable
  bases.
category: Platform Automation
version: 1.0.0
---

# Airtable Automation & Base Design

## Base Architecture

### Workspace Organization
- **Shared base**: Central source of truth (read/write controlled by roles)
- **Interface tab**: Customer-facing views and forms (restrict to needed fields)
- **Data tabs**: Normalized tables with clean schemas
- **System tabs**: Hidden from users (webhooks, logs, configs)

### Table Design Patterns
- **Entities table**: Records with unique identifiers and metadata
- **Junction table**: Many-to-many relationships between entities
- **Config table**: Settings and parameters (single row per config)
- **Audit table**: Track record changes for compliance

### Field Types & Usage
- **Single select**: Status, type, category (predefined options)
- **Multiple select**: Tags, skills, interests (multi-value)
- **Linked records**: Relationships to other tables
- **Lookup**: Read fields from linked records
- **Count**: Aggregate linked record counts
- **Rollup**: Sum, avg, min, max of linked records
- **Formula**: Calculated fields (date math, string ops, conditionals)
- **Checkbox**: Boolean flags (is_active, is_verified)
- **Email/Phone**: Validated contact fields
- **URL**: Links with automatic title preview
- **Attachment**: File uploads (max 5 per cell)

## Automation Framework

### Trigger Types
- **Record created**: New record added to table
- **Record modified**: Any field changed (specify fields for efficiency)
- **Form submitted**: New form submission received
- **Recurring**: Cron-like scheduling (hourly, daily, weekly, monthly)
- **Webhook**: External system sends data
- **Button**: User clicks automation button in record

### Action Sequences
1. **Conditional logic**:
   - If status = "new", then send email to team
   - If amount > $5000, then create task for manager
   - If date is today, then update status to "active"

2. **Multi-step flows**:
   - Create record in Table A
   - Then send email
   - Then create task in Table B
   - Then notify Slack

3. **Error handling**:
   - Use branching to test conditions before actions
   - Add wait steps to prevent race conditions
   - Test automations with sample data before enabling

### Common Automation Patterns
- **Lead scoring**: Record created → Calculate score → Update status
- **Task assignment**: Deal stage change → Create task → Assign → Notify
- **Email sequences**: Form submit → Check conditions → Send email → Log
- **Approval workflows**: Record created → Notify approver → Wait for response
- **Sync to external**: Record modified → Send to CRM → Create contact

## Interface Design

### Interface Types
- **Grid**: Spreadsheet-like table editing
- **Form**: Data entry form with validation
- **Calendar**: Visual schedule or timeline
- **Gallery**: Card-based browsing
- **Kanban**: Drag-and-drop by status
- **Details panel**: Record view with related items

### Field Visibility & Permissions
- Show only essential fields per interface (reduce clutter)
- Hide formula/lookup fields that are for backend use only
- Lock critical fields (IDs, dates) in interface to prevent edits
- Use conditional visibility to show fields based on status

### Mobile Optimization
- Interfaces are responsive but optimize for phone
- Limit to 3-5 fields per form view
- Use buttons for actions (easier than clicking small UIs)
- Test on actual phone before sharing with users

## Scripting APIs

### Field Types in Scripts
```javascript
// Get field value
const name = record.getCellValue("Name");
const items = record.getCellValue("Linked Items");  // Array

// Write to field
await table.updateRecordsAsync([{
  id: record.id,
  fields: { "Name": "New Value", "Status": "Done" }
}]);

// Create new record
const newRecord = await table.createRecordsAsync([{
  fields: { "Name": "Test", "Email": "test@example.com" }
}]);
```

### Common Scripting Patterns
- **Bulk update**: Loop through records, apply transformation
- **Import data**: Parse CSV, create records from array
- **Data sync**: Fetch from API, update matching records
- **Validation**: Check field constraints, log errors
- **Notification**: Parse records, send summary email

### Script Blocks Vs Extensions
- **Script blocks**: Internal automation, data transformation
- **Scripting extension**: User-triggered scripts with UI
- **Limits**: Script runs timeout after 30 seconds
- **Permissions**: Scripts inherit user permissions (careful with shared bases)

## Integration Patterns

### Zapier Integration
- Create triggers from Airtable (record created/updated)
- Send to email, webhook, or third-party service
- Common: Airtable → Slack, Airtable → Email, Airtable → Google Sheets

### Webhook Automation
1. External system sends HTTP POST to Airtable webhook
2. Airtable receives JSON payload
3. Automation triggers on webhook event
4. Process data and create/update records

### API-First Workflows
- Use REST API for programmatic access
- OAuth authentication for user-level tokens
- Rate limits: 5 req/sec, burst to 30
- Batch operations: Create up to 10 records per request

## Deployment Best Practices

### Version Control
- No direct version control (unlike code)
- Document base changes in a "Changelog" table
- Create snapshots: duplicate base, archive old version
- Use base sharing to track who made what changes

### Sharing & Permissions
- **Editor**: Create, edit, delete records (can't manage base structure)
- **Commenter**: Edit only allowed records, add comments
- **Read only**: View only, no edits
- **Owner**: Manage base structure, automations, sharing

### Testing Before Launch
1. Create sandbox base with test data
2. Enable automation
3. Trigger manually (if possible) or wait for scheduled run
4. Verify results in tables and external systems
5. Check error logs in Automation history
6. Deploy to production base

### Performance Monitoring
- Enable "Automation Activity" to track runs and failures
- Set up email notifications for automation errors
- Monitor webhook retry logs (Airtable retries 3x)
- Use Scripting extension to log manual processes

## Advanced Features

### Linked Records & Rollups
- Create many-to-many relationships via junction tables
- Use Count field to show number of linked records
- Rollup can aggregate: sum, count, avg, max, min, max, concatenate
- Example: Contacts ←→ Projects (junction: Contact-Project mapping)

### Formula Recipes
```
# Status badge color
IF({Status} = "Done", "green", IF({Status} = "In Progress", "blue", "red"))

# Days until deadline
DAYS({Deadline}, TODAY())

# Full name from first/last
CONCATENATE({First Name}, " ", {Last Name})

# Calculate age
INT((TODAY() - {Birth Date}) / 365.25)
```

### Conditional Coloring
- Color rows based on formula results (red = overdue, green = complete)
- Highlight high-value opportunities (amount > threshold)
- Visual status indicators (status = "blocked" → red)

## Migration & Maintenance

### Importing Data
1. Prepare CSV with headers matching field names
2. Use table import tool (drag CSV onto base)
3. Map columns to existing fields or create new
4. Fix linked record references manually (CSV import can't auto-link)
5. Verify data integrity with a quick filter/sort check

### Archival Strategy
- Create "Archive" workspace separate from active bases
- Move closed projects/deals to archive base
- Keep references via URLs (Airtable links are stable)
- Run annual cleanup to remove obsolete records

### Audit & Compliance
- Enable "Comments" and use for decision logging
- Track who made changes via "Last Modified By" field
- Archive snapshots of critical data monthly
- Document all automation logic in a "System Design" table
