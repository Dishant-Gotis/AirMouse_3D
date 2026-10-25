---
skill_name: ai-automation-integration
description: AI in automation for LLM classification, content generation, data extraction, and intelligent routing
category: Workflow Automation
version: 1.0.0
---

# AI & Automation Integration

## Overview
AI enhances automation with intelligence. This guide covers LLM classification, content generation, and extraction workflows.

## Pattern 1: AI Content Classification

**Incoming message → Classify intent → Route appropriately**

```javascript
async function classifyAndRoute(message) {
  const openai = require('openai');

  const classification = await openai.createChatCompletion({
    model: 'gpt-4',
    messages: [
      {
        role: 'system',
        content: `Classify this customer message into one category:
        - billing: payment, invoice, pricing questions
        - technical: bugs, feature requests, how-to
        - account: login, password, account management
        - sales: interest in products, demos, pricing
        - support: general questions, help needed
        - complaint: dissatisfied, want refund, issues
        `
      },
      {
        role: 'user',
        content: message.body
      }
    ],
    max_tokens: 50
  });

  const category = classification.choices[0].message.content.toLowerCase();

  // Route based on classification
  const routes = {
    billing: { team: 'billing', priority: 'high' },
    technical: { team: 'engineering', priority: 'medium' },
    account: { team: 'support', priority: 'high' },
    sales: { team: 'sales', priority: 'medium' },
    support: { team: 'support', priority: 'medium' },
    complaint: { team: 'cso', priority: 'critical' }
  };

  const route = routes[category] || routes.support;

  // Auto-respond based on category
  await sendAutoResponse(message.from, category);

  // Create ticket
  await createTicket({
    ...message,
    category: category,
    assignedTo: route.team,
    priority: route.priority
  });
}
```

## Pattern 2: LLM Content Generation

**Data + template → AI generates polished content**

```javascript
async function generateEmail(context) {
  const openai = require('openai');

  const prompt = `
Generate a professional outreach email based on this context:
- Recipient: ${context.recipientName}
- Company: ${context.company}
- Pain point: ${context.painPoint}
- Tone: ${context.tone || 'professional'}
- Length: 150-200 words

Make it personalized and compelling.
  `;

  const response = await openai.createChatCompletion({
    model: 'gpt-4',
    messages: [
      { role: 'user', content: prompt }
    ],
    max_tokens: 300
  });

  const emailBody = response.choices[0].message.content;

  // Save as draft
  await saveDraft({
    to: context.recipientEmail,
    subject: `Helping ${context.company} with ${context.painPoint}`,
    body: emailBody,
    draftId: generateId()
  });

  return { draftId, preview: emailBody };
}
```

## Pattern 3: Document Data Extraction

**PDF/image → Extract structured data**

```javascript
async function extractContractTerms(contractPdf) {
  const openai = require('openai');

  // Convert PDF to base64 or use OCR first
  const documentBase64 = await pdfToBase64(contractPdf);

  const response = await openai.createChatCompletion({
    model: 'gpt-4-vision',
    messages: [
      {
        role: 'user',
        content: [
          {
            type: 'image_url',
            image_url: { url: `data:image/png;base64,${documentBase64}` }
          },
          {
            type: 'text',
            text: `Extract key contract terms as JSON:
            {
              "parties": [],
              "startDate": "",
              "endDate": "",
              "paymentTerms": "",
              "renewalTerms": "",
              "terminationClause": "",
              "liabilityCap": ""
            }`
          }
        ]
      }
    ],
    max_tokens: 1000
  });

  const extracted = JSON.parse(response.choices[0].message.content);

  // Store in database
  await saveExtractedTerms(contractPdf.id, extracted);

  return extracted;
}
```

## Pattern 4: Smart Segmentation

**AI analyzes customer data → Creates intelligent segments**

```javascript
async function createAISegments(customers) {
  const openai = require('openai');

  const customerSummary = customers.map(c => ({
    id: c.id,
    companySize: c.companySize,
    industry: c.industry,
    productUsage: c.usagePercentage,
    nps: c.npsScore,
    renewalDate: c.renewalDate,
    pipelineValue: c.potentialUpsell
  }));

  const response = await openai.createChatCompletion({
    model: 'gpt-4',
    messages: [
      {
        role: 'user',
        content: `Based on this customer data, create 4-5 segments with:
        - Segment name
        - Characteristics
        - Recommended actions
        - Customer IDs

        Data: ${JSON.stringify(customerSummary)}`
      }
    ],
    max_tokens: 2000
  });

  const segments = parseSegments(response.choices[0].message.content);

  // Create segments in CRM
  for (const segment of segments) {
    await createSegment({
      name: segment.name,
      description: segment.characteristics,
      customers: segment.customerIds,
      recommendedActions: segment.actions
    });
  }

  return segments;
}
```

## Pattern 5: Intelligent Routing

**LLM routes complex cases to best agent**

```javascript
async function intelligentRouting(ticket) {
  const openai = require('openai');

  // Get available agents and their skills
  const agents = await getAvailableAgents();

  const agentSkills = agents.map(a => ({
    id: a.id,
    name: a.name,
    skills: a.skills,
    currentLoad: a.activeTickets.length
  }));

  const response = await openai.createChatCompletion({
    model: 'gpt-4',
    messages: [
      {
        role: 'user',
        content: `Route this support ticket to the best agent:

Ticket: ${ticket.subject}
Description: ${ticket.body}

Available agents:
${JSON.stringify(agentSkills)}

Return JSON: { agentId, reasoning }`
      }
    ],
    max_tokens: 300
  });

  const routing = JSON.parse(response.choices[0].message.content);

  await assignTicket(ticket.id, routing.agentId);

  return routing;
}
```

## Best Practices

1. **Use GPT-4 for complex logic** — Not GPT-3.5
2. **Validate AI output** — Don't trust blindly
3. **Human-in-loop** — For critical decisions
4. **Cache prompts** — Save costs
5. **Monitor hallucinations** — LLMs make mistakes
6. **Version your prompts** — Track what works
7. **Set guardrails** — Filter inappropriate content
8. **Use temperature wisely** — Higher = more creative/unpredictable
9. **Batch requests** — More efficient
10. **Keep humans in control** — AI augments, not replaces

