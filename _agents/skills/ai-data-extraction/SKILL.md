---
skill_name: ai-data-extraction
description: Data extraction: structured extraction from unstructured text, Pydantic, validation
category: AI & LLM
version: 1.0.0
---

# Data Extraction from Unstructured Text

## Pydantic-Based Extraction

```python
from pydantic import BaseModel, Field, validator
from typing import List, Optional

class Person(BaseModel):
    name: str = Field(..., min_length=1)
    email: str = Field(..., regex=r"^[\w\.-]+@[\w\.-]+\.\w+$")
    age: Optional[int] = Field(None, ge=0, le=150)
    phone: Optional[str] = None

    @validator('name')
    def name_valid(cls, v):
        if not all(c.isalpha() or c.isspace() for c in v):
            raise ValueError('Name must contain only letters')
        return v.strip().title()

def extract_person(text: str) -> Person:
    """Extract person from text."""
    prompt = f"""
Extract person information:
{text}

Return JSON: {{"name": "...", "email": "...", "age": ..., "phone": "..."}}
"""
    response = client.chat.completions.create(
        model="gpt-4",
        response_format={"type": "json_object"},
        messages=[{"role": "user", "content": prompt}]
    )

    data = json.loads(response.choices[0].message.content)
    return Person(**data)  # Validates automatically

person = extract_person("John Smith (john@example.com) is 30 years old")
```

## Batch Extraction

```python
class BatchExtractor:
    def __init__(self, schema: BaseModel):
        self.schema = schema

    def extract_batch(self, texts: list[str]) -> list[dict]:
        """Extract from multiple texts."""
        results = []

        for text in texts:
            try:
                extracted = self._extract_single(text)
                results.append({"success": True, "data": extracted})
            except Exception as e:
                results.append({"success": False, "error": str(e)})

        return results

    def _extract_single(self, text: str) -> dict:
        prompt = f"""
Extract structured data:
{text}

Return JSON matching this schema: {self.schema.schema()}
"""
        response = client.chat.completions.create(
            model="gpt-4",
            response_format={"type": "json_object"},
            messages=[{"role": "user", "content": prompt}]
        )

        data = json.loads(response.choices[0].message.content)
        return self.schema(**data).dict()

extractor = BatchExtractor(Person)
results = extractor.extract_batch(text_list)
```

## Error Handling & Retry

```python
class RobustExtractor:
    def __init__(self, schema: BaseModel, max_retries: int = 3):
        self.schema = schema
        self.max_retries = max_retries

    def extract_with_retry(self, text: str) -> dict:
        """Extract with retry on validation failure."""
        for attempt in range(self.max_retries):
            try:
                return self._extract(text)
            except ValueError as e:
                if attempt == self.max_retries - 1:
                    # Last attempt, try different approach
                    return self._extract_with_fallback(text)

                # Retry with clarification
                text = f"Clarify and retry:\n{text}"

    def _extract(self, text: str) -> dict:
        prompt = f"Extract: {text}\nReturn JSON: ..."
        response = client.chat.completions.create(
            model="gpt-4",
            response_format={"type": "json_object"},
            messages=[{"role": "user", "content": prompt}]
        )

        data = json.loads(response.choices[0].message.content)
        return self.schema(**data).dict()

    def _extract_with_fallback(self, text: str) -> dict:
        """Fallback: extract with more lenient schema."""
        from typing import Any

        class LenientSchema(BaseModel):
            data: dict[str, Any]

        # Extract as generic dict
        return {"raw_data": json.loads(client.chat.completions.create(
            model="gpt-4",
            response_format={"type": "json_object"},
            messages=[{"role": "user", "content": f"Extract all data: {text}"}]
        ).choices[0].message.content)}
```

## Multi-Step Extraction

```python
class ChainedExtractor:
    def __init__(self, llm):
        self.llm = llm

    def extract_hierarchical(self, text: str) -> dict:
        """Extract with hierarchy."""
        # Step 1: Extract categories
        categories = self._extract_categories(text)

        # Step 2: Extract within each category
        results = {}
        for category in categories:
            results[category] = self._extract_for_category(text, category)

        return results

    def _extract_categories(self, text: str) -> list[str]:
        prompt = f"Identify data categories in: {text}\nReturn: category1, category2"
        response = self.llm.predict(prompt)
        return [c.strip() for c in response.split(",")]

    def _extract_for_category(self, text: str, category: str) -> dict:
        prompt = f"Extract {category} data from: {text}\nReturn JSON"
        response = self.llm.predict(prompt)
        return json.loads(response)
```

## Key Takeaways

- Pydantic validates during extraction
- Batch extraction handles multiple texts
- Retry logic ensures completeness
- Fallback schemas handle edge cases
- Hierarchical extraction maintains structure
