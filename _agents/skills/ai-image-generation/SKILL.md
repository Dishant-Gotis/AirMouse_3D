---
skill_name: ai-image-generation
description: Image generation: DALL-E, Stable Diffusion, Midjourney API, prompt engineering
category: AI & LLM
version: 1.0.0
---

# AI Image Generation

## DALL-E

```python
from openai import OpenAI
from PIL import Image
import requests
from io import BytesIO

client = OpenAI()

def generate_image(prompt: str, size: str = "1024x1024", quality: str = "standard") -> str:
    """Generate image with DALL-E."""
    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size=size,
        quality=quality,
        n=1
    )

    return response.data[0].url

def generate_and_save(prompt: str, output_file: str = "output.png"):
    """Generate and save image."""
    url = generate_image(prompt)

    response = requests.get(url)
    img = Image.open(BytesIO(response.content))
    img.save(output_file)

    return output_file

# Generate
url = generate_image("A serene mountain landscape at sunset")

# Edit existing image
def edit_image(image_path: str, mask_path: str, prompt: str):
    """Edit image with inpainting."""
    with open(image_path, "rb") as img_file:
        with open(mask_path, "rb") as mask_file:
            response = client.images.create_variation(
                image=img_file,
                mask=mask_file,
                prompt=prompt,
                n=1,
                size="1024x1024"
            )

    return response.data[0].url
```

## Stable Diffusion

```python
import requests

class StableDiffusionGenerator:
    def __init__(self, api_key: str = "your_key"):
        self.api_key = api_key
        self.engine_id = "stable-diffusion-v1-6"
        self.api_host = "https://api.stability.ai"

    def generate(self, prompt: str, negative_prompt: str = "") -> bytes:
        """Generate image with Stable Diffusion."""
        url = f"{self.api_host}/v1/generation/{self.engine_id}/text-to-image"

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        body = {
            "steps": 40,
            "width": 512,
            "height": 512,
            "seed": 0,
            "cfg_scale": 7.0,
            "samples": 1,
            "text_prompts": [
                {"text": prompt, "weight": 1.0},
                {"text": negative_prompt, "weight": -1.0}
            ]
        }

        response = requests.post(url, json=body, headers=headers)
        return response.content

generator = StableDiffusionGenerator()
image_bytes = generator.generate("A futuristic city")
```

## Prompt Engineering for Images

```python
class ImagePromptBuilder:
    @staticmethod
    def build_detailed_prompt(
        subject: str,
        style: str,
        quality: str,
        lighting: str,
        composition: str
    ) -> str:
        """Build detailed image prompt."""
        template = f"""
{subject}
art style: {style}
quality: {quality}
lighting: {lighting}
composition: {composition}
"""
        return template.strip()

    @staticmethod
    def build_from_keywords(**kwargs) -> str:
        """Build from keyword dict."""
        parts = []

        for key, value in kwargs.items():
            if value:
                parts.append(f"{key}: {value}")

        return ", ".join(parts)

builder = ImagePromptBuilder()

prompt = builder.build_detailed_prompt(
    subject="A woman in a forest",
    style="oil painting",
    quality="high quality, detailed",
    lighting="golden hour light",
    composition="rule of thirds"
)

image_url = generate_image(prompt)
```

## Batch Generation

```python
import asyncio

class BatchImageGenerator:
    def __init__(self, llm):
        self.llm = llm

    async def generate_batch(self, descriptions: list[str]) -> list[str]:
        """Generate multiple images."""
        tasks = [generate_image_async(desc) for desc in descriptions]
        return await asyncio.gather(*tasks)

    def generate_variations(self, prompt: str, num_variations: int = 5) -> list[str]:
        """Generate variations of same prompt."""
        variation_prompts = []

        for i in range(num_variations):
            varied = self.llm.predict(
                f"Variation {i+1} of: {prompt}\nReturn varied prompt only:"
            )
            variation_prompts.append(varied)

        urls = [generate_image(p) for p in variation_prompts]
        return urls

async def generate_image_async(prompt: str) -> str:
    """Async image generation."""
    return generate_image(prompt)

generator = BatchImageGenerator(llm)

# Generate series
descriptions = ["sunset", "sunrise", "night sky"]
urls = asyncio.run(generator.generate_batch(descriptions))
```

## Key Takeaways

- DALL-E provides high-quality generation
- Stable Diffusion is open-source alternative
- Prompt engineering significantly improves results
- Batch generation scales to multiple images
- Variations explore creative alternatives
