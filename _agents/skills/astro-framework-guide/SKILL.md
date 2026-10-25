---
skill_name: Astro Framework Guide
description: Build static sites with Astro, content collections, islands, and integrations
category: Frontend
version: 1.0.0
---

# Astro Framework Guide

## Project Setup

```bash
npm create astro@latest my-project
cd my-project
npm run dev
```

## Pages and Routing

```typescript
// src/pages/index.astro
---
const title = "Home"
---
<html>
  <head><title>{title}</title></head>
  <body>
    <h1>{title}</h1>
  </body>
</html>

// src/pages/posts/[slug].astro
---
export async function getStaticPaths() {
  return [
    { params: { slug: 'post-1' } },
    { params: { slug: 'post-2' } }
  ]
}

const { slug } = Astro.params
---
<h1>{slug}</h1>
```

## Components

```astro
// src/components/Card.astro
---
interface Props {
  title: string
}

const { title } = Astro.props
---

<div class="card">
  <h2>{title}</h2>
  <slot />
</div>

<style>
  .card {
    border: 1px solid #ccc;
    padding: 1rem;
  }
</style>
```

## Content Collections

```typescript
// src/content/config.ts
import { defineCollection, z } from 'astro:content'

const postsCollection = defineCollection({
  schema: z.object({
    title: z.string(),
    pubDate: z.date(),
    description: z.string(),
    author: z.string()
  })
})

export const collections = {
  'posts': postsCollection
}
```

```typescript
// src/pages/posts/[slug].astro
import { getCollection } from 'astro:content'

export async function getStaticPaths() {
  const posts = await getCollection('posts')
  return posts.map(post => ({
    params: { slug: post.slug },
    props: { post }
  }))
}

const { post } = Astro.props
const { Content } = await post.render()
```

## Islands Architecture

```astro
// Interactive component
---
import Counter from '../components/Counter.jsx'
---

<main>
  <h1>Static content</h1>
  <Counter client:load />
</main>
```

## Integrations

```bash
npm run astro add react
npm run astro add vue
npm run astro add svelte
npm run astro add tailwind
```

## Build and Deploy

```bash
npm run build    # Generate static site
npm run preview  # Preview production build
```

## Production Checklist

- [ ] Optimize images
- [ ] Set up sitemap
- [ ] Configure analytics
- [ ] Create robots.txt
- [ ] Deploy to CDN
