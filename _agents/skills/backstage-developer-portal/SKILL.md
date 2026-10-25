---
skill_name: Backstage Developer Portal
description: Build service catalogs, templates, plugins, and TechDocs with Backstage
category: Platform Engineering
version: 1.0.0
---

# Backstage Developer Portal

## Overview
Backstage creates unified developer platforms. Master service catalogs, templates, and plugins.

## Service Catalog

### Entity Model

```yaml
apiVersion: backstage.io/v1alpha1
kind: Component
metadata:
  name: user-service
  description: User management service
  annotations:
    github.com/project-slug: company/user-service
    pagerduty.com/integration-key: integration-key-123
spec:
  type: service
  owner: user-team
  lifecycle: production
  providesApis:
    - user-api
  dependsOn:
    - postgresql-db
    - redis-cache
```

### Catalog Discovery

- YAML files in repositories
- Automatic GitHub discovery
- Webhook-based registration
- Custom ingestion

## Scaffolder Templates

### Template Definition

```yaml
apiVersion: scaffolder.backstage.io/v1beta3
kind: Template
metadata:
  name: create-service
  title: Create a New Service
spec:
  owner: platform-team
  type: service
  parameters:
    - title: Service Details
      required:
        - name
        - owner
      properties:
        name:
          type: string
          title: Service Name
        owner:
          type: string
          title: Owner Team
  steps:
    - id: create-repo
      name: Create Repository
      action: publish:github:pull-request
      input:
        repoUrl: github.com?repo=${{ parameters.name }}
    - id: register-catalog
      name: Register in Catalog
      action: catalog:register
      input:
        repoContentsUrl: ${{ steps.create-repo.output.repoContentsUrl }}
```

## Plugins Architecture

### Custom Plugin

```typescript
import {
  createPlugin,
  createRoutableExtension,
} from '@backstage/core-plugin-api';

export const examplePlugin = createPlugin({
  id: 'example',
  routes: {
    root: createRoutableExtension({
      name: 'ExamplePage',
      component: () => import('./pages/ExamplePage').then(m => m.ExamplePage),
      mountPoint: exampleRouteRef,
    }),
  },
});
```

## TechDocs

### Documentation as Code

```markdown
# Service Documentation

## Overview
Service purpose and high-level design

## API Reference
Endpoints, request/response formats

## Deployment
How to deploy and configure

## Troubleshooting
Common issues and solutions
```

### Publishing Docs

```
1. Write Markdown in repo
2. Configure mkdocs.yml
3. Push to repository
4. Backstage automatically builds and hosts
```

## Production Checklist

- [ ] Define service catalog schema
- [ ] Create scaffolder templates for common patterns
- [ ] Develop custom plugins for your workflows
- [ ] Set up automated docs publishing
- [ ] Configure RBAC for catalog
- [ ] Integrate with deployment systems
- [ ] Monitor catalog completeness
- [ ] Document plugin development
- [ ] Establish template governance
- [ ] Plan for plugin ecosystem growth
