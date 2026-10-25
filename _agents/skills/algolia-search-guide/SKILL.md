---
skill_name: Algolia Search Guide
description: Implement fast search with Algolia indexing, facets, filters, and analytics
category: Backend
version: 1.0.0
---

# Algolia Search Guide

## Setup

```bash
npm install algoliasearch
```

```typescript
import algoliasearch from 'algoliasearch'

const client = algoliasearch('APP_ID', 'API_KEY')
const index = client.initIndex('products')
```

## Index Data

```typescript
async function indexProducts(products) {
  const records = products.map((p, i) => ({
    objectID: i.toString(),
    name: p.name,
    price: p.price,
    category: p.category,
    popularity: p.sales
  }))

  await index.saveObjects(records)
}
```

## Search

```typescript
async function search(query) {
  const results = await index.search(query, {
    facetFilters: [['category:Electronics']],
    numericFilters: ['price < 1000'],
    hitsPerPage: 20
  })

  return results.hits
}
```

## Faceted Search

```typescript
const results = await index.search('laptop', {
  facets: ['category', 'brand'],
  facetFilters: [['category:Electronics', 'category:Computers']]
})

console.log(results.facets)
```

## Analytics

```typescript
// Algolia tracks searches automatically
// View in Analytics dashboard
```

## Production Checklist

- [ ] Set up separate indices for dev/prod
- [ ] Configure facets before indexing
- [ ] Monitor search analytics
- [ ] Implement search suggestions
- [ ] Use real-time index
