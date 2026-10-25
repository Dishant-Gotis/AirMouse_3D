---
skill_name: AI Image Generation Guide
description: Generate images with Midjourney, DALL-E, and Stable Diffusion including prompting techniques and workflow optimization
category: Creative & Media
version: 1.0.0
---

# AI Image Generation Guide

## Overview
AI image generation transforms content creation. Master prompting, model selection, and post-production for professional results.

## Midjourney Prompting

### Prompt Structure

```
/imagine prompt: [SUBJECT] [STYLE] [MEDIUM] [LIGHTING] [COMPOSITION] [QUALITY]

Examples:
1. Minimalist design:
   /imagine prompt: sleek modern workspace, minimalist design,
   clean lines, neutral colors, natural light, photography,
   professional, high quality, 8k

2. Cinematic:
   /imagine prompt: futuristic city, neon lights, cyberpunk aesthetic,
   cinematic lighting, dramatic shadows, 35mm film, sci-fi, trending
   on artstation, highly detailed

3. Digital art:
   /imagine prompt: fantasy warrior, detailed armor, epic pose,
   vibrant colors, digital painting, fantasy art, trending,
   artstation quality, concept art
```

### Advanced Parameters

```
--aspect 16:9           # Aspect ratio
--no objects            # Exclude specific elements
--quality 2             # Quality multiplier (0.25, 0.5, 1, 2)
--chaos 50              # Creativity level (0-100)
--iw 0.5                # Image weight (relative to text)
--style raw             # Alternative styles
--niji                  # Anime model
```

## DALL-E Prompting

### Effective Prompts

```
# Photography-focused
"A professional photograph of [subject], shot on [camera],
[lighting conditions], [composition], [film stock or style],
award-winning, detailed, sharp focus"

# Illustration style
"A detailed digital illustration of [subject] in [style],
trending on ArtStation, concept art, professional artist,
vibrant colors, high quality"

# 3D rendering
"A high-quality 3D render of [subject], octane render,
cinematic lighting, volumetric lights, depth of field,
professional, trending on CGTrader"
```

## Stable Diffusion

### Model Selection

```
# Model types
Realistic Vision: Photorealistic images
Dreamshaper: Balanced quality and creativity
Elysium Anime: High-quality anime
Protogen: High quality, versatile

# Negative prompts
negative_prompt: "blurry, low quality, distorted,
ugly, deformed, text, watermark, artificial"
```

## Workflow Optimization

```python
class ImageGenerationWorkflow:
    def __init__(self, model='midjourney'):
        self.model = model
        self.image_queue = []

    def generate_batch(self, prompts, variations=2):
        """Generate multiple images efficiently"""
        for prompt in prompts:
            for _ in range(variations):
                self.image_queue.append({
                    'prompt': prompt,
                    'generated': False,
                    'selected': False
                })

    def upscale_best(self, images):
        """Upscale highest quality results"""
        best = sorted(images, key=lambda x: x['quality'], reverse=True)[:5]
        return [self.upscale(img) for img in best]

    def get_prompt_elements(self):
        """Essential prompt elements"""
        return {
            'subject': 'What is being created?',
            'style': 'Art style or movement',
            'medium': 'How it\'s made (photo, oil painting, etc)',
            'lighting': 'Light conditions',
            'composition': 'Framing and perspective',
            'quality': 'Detail level and quality indicators'
        }
```

## Post-Processing

```python
from PIL import Image, ImageEnhance

class ImagePostProcessor:
    def __init__(self, image_path):
        self.img = Image.open(image_path)

    def enhance_clarity(self, factor=1.5):
        """Increase sharpness"""
        enhancer = ImageEnhance.Sharpness(self.img)
        return enhancer.enhance(factor)

    def enhance_colors(self, factor=1.2):
        """Increase color saturation"""
        enhancer = ImageEnhance.Color(self.img)
        return enhancer.enhance(factor)

    def adjust_contrast(self, factor=1.1):
        """Adjust contrast"""
        enhancer = ImageEnhance.Contrast(self.img)
        return enhancer.enhance(factor)

    def remove_artifacts(self):
        """Clean up common AI generation issues"""
        # Use inpainting or manual cleanup
        pass

    def composite_elements(self, foreground, background):
        """Combine multiple generations"""
        pass
```

## Best Practices

```
1. Iteration Strategy:
   - Generate 4-9 variations
   - Select best 2-3 results
   - Upscale selected images
   - Post-process for refinement

2. Prompt Optimization:
   - Start specific and simple
   - Add style references
   - Use artist names
   - Include quality boosters

3. Model Selection:
   - Realistic photography → Realistic Vision
   - Artistic → Dreamshaper/Custom
   - Anime → Elysium Anime
   - Fast prototyping → Stable Diffusion
```

## Production Checklist

- [ ] Master basic prompting
- [ ] Learn model-specific syntax
- [ ] Build prompt templates
- [ ] Test different styles
- [ ] Post-process results
- [ ] Maintain prompt log
- [ ] Iterate on feedback
- [ ] Upscale best images
- [ ] Verify output quality
- [ ] Document process
