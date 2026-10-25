---
skill_name: ai-safety-guardrails
description: AI safety: constitutional AI, RLHF principles, output filtering, toxicity detection
category: AI & LLM
version: 1.0.0
---

# AI Safety: Guardrails & Alignment Techniques

## Constitutional AI (CAI)

Align models with principles:

```python
class ConstitutionalAI:
    def __init__(self, model, principles: list[str]):
        self.model = model
        self.principles = principles

    def evaluate_response(self, prompt: str, response: str) -> dict:
        """Evaluate response against constitution."""
        violations = []

        for principle in self.principles:
            eval_prompt = f"""
Principle: {principle}
Response: {response}

Does this response violate the principle? (yes/no):
"""
            violation = "yes" in self.model.predict(eval_prompt).lower()
            if violation:
                violations.append(principle)

        return {
            "is_valid": len(violations) == 0,
            "violations": violations,
            "num_violations": len(violations)
        }

    def generate_safe_response(self, prompt: str, max_attempts: int = 3):
        """Generate response until it passes all checks."""
        for attempt in range(max_attempts):
            response = self.model.predict(prompt)

            eval = self.evaluate_response(prompt, response)
            if eval["is_valid"]:
                return response

            # Ask model to fix violations
            fix_prompt = f"""
Original response: {response}
Violates: {', '.join(eval['violations'])}

Provide improved response that doesn't violate these principles:
"""
            response = self.model.predict(fix_prompt)

        return "Unable to generate safe response"

principles = [
    "Do not provide instructions for illegal activities",
    "Do not generate hateful content",
    "Do not provide medical advice",
    "Be factually accurate"
]

cai = ConstitutionalAI(model, principles)
safe_response = cai.generate_safe_response("Your prompt")
```

## RLHF (Reinforcement Learning from Human Feedback)

```python
class RLHFTrainer:
    def __init__(self, model, reward_model):
        self.model = model
        self.reward_model = reward_model

    def generate_and_rank(self, prompt: str, num_samples: int = 4):
        """Generate multiple responses and rank by reward."""
        responses = []
        rewards = []

        for _ in range(num_samples):
            response = self.model.generate(prompt, temperature=0.9)
            responses.append(response)

            reward = self.reward_model.score(prompt, response)
            rewards.append(reward)

        # Sort by reward
        ranked = sorted(
            zip(responses, rewards),
            key=lambda x: x[1],
            reverse=True
        )
        return ranked

    def create_preference_pairs(self, prompts: list[str], num_samples: int = 4):
        """Create preference data for RLHF."""
        preference_pairs = []

        for prompt in prompts:
            ranked = self.generate_and_rank(prompt, num_samples)

            for i in range(len(ranked) - 1):
                preferred = ranked[i][0]
                dispreferred = ranked[i + 1][0]

                preference_pairs.append({
                    "prompt": prompt,
                    "preferred": preferred,
                    "dispreferred": dispreferred,
                    "score_diff": ranked[i][1] - ranked[i + 1][1]
                })

        return preference_pairs

trainer = RLHFTrainer(model, reward_model)
pairs = trainer.create_preference_pairs(prompts)
```

## Content Filtering

Detect and filter problematic content:

```python
from typing import Tuple

class ContentFilter:
    def __init__(self, sensitive_keywords: list[str]):
        self.keywords = sensitive_keywords

    def filter_response(self, response: str, safety_level: str = "high") -> Tuple[str, bool]:
        """Filter response, return filtered text and is_safe flag."""
        is_safe = True

        # Keyword detection
        for keyword in self.keywords:
            if keyword.lower() in response.lower():
                is_safe = False
                # Redact keyword
                response = response.replace(keyword, "[REDACTED]")

        # Heuristic checks
        if safety_level == "high":
            # Check for suspicious patterns
            suspicious_patterns = ["follow these instructions", "ignore your guidelines"]
            for pattern in suspicious_patterns:
                if pattern in response.lower():
                    is_safe = False

        return response, is_safe

filter = ContentFilter([
    "password",
    "credit card",
    "social security number"
])

response, is_safe = filter.filter_response("Your credit card number is 1234...")
print(f"Safe: {is_safe}, Filtered: {response}")
```

## Toxicity Detection

```python
from transformers import pipeline

class ToxicityDetector:
    def __init__(self, model_name="facebook/roberta-hate-speech-classification"):
        self.classifier = pipeline("sentiment-analysis", model=model_name)

    def detect_toxicity(self, text: str, threshold: float = 0.5) -> dict:
        """Detect toxicity in text."""
        result = self.classifier(text[:512])[0]  # Truncate for model

        is_toxic = result["label"] == "HATE" and result["score"] > threshold

        return {
            "is_toxic": is_toxic,
            "confidence": result["score"],
            "label": result["label"]
        }

    def filter_batch(self, texts: list[str], threshold: float = 0.5):
        """Filter batch of texts."""
        filtered = []

        for text in texts:
            toxicity = self.detect_toxicity(text, threshold)
            if not toxicity["is_toxic"]:
                filtered.append(text)

        return filtered

detector = ToxicityDetector()
result = detector.detect_toxicity("This is great content")
print(f"Toxic: {result['is_toxic']}, Confidence: {result['confidence']:.2%}")
```

## PII Detection & Redaction

```python
import re
from typing import List, Dict

class PIIDetector:
    def __init__(self):
        self.patterns = {
            "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
            "phone": r"\d{3}[-.\s]?\d{3}[-.\s]?\d{4}",
            "ssn": r"\d{3}-\d{2}-\d{4}",
            "credit_card": r"\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}",
            "ip_address": r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}"
        }

    def detect_pii(self, text: str) -> Dict[str, List[str]]:
        """Detect all PII in text."""
        pii_found = {}

        for pii_type, pattern in self.patterns.items():
            matches = re.findall(pattern, text)
            if matches:
                pii_found[pii_type] = matches

        return pii_found

    def redact_pii(self, text: str) -> str:
        """Redact all PII from text."""
        for pii_type, pattern in self.patterns.items():
            text = re.sub(pattern, f"[{pii_type.upper()}]", text)

        return text

detector = PIIDetector()
text = "Contact me at john@example.com or 555-123-4567"
pii = detector.detect_pii(text)
redacted = detector.redact_pii(text)
print(f"PII found: {pii}")
print(f"Redacted: {redacted}")
```

## Adversarial Input Detection

```python
class AdversarialDetector:
    def __init__(self, model):
        self.model = model

    def is_jailbreak_attempt(self, prompt: str) -> bool:
        """Detect potential jailbreak prompts."""
        red_flags = [
            "ignore previous instructions",
            "pretend you are",
            "ignore your guidelines",
            "act as if",
            "system prompt is",
            "do exactly what i say"
        ]

        prompt_lower = prompt.lower()
        return any(flag in prompt_lower for flag in red_flags)

    def detect_prompt_injection(self, prompt: str) -> bool:
        """Detect prompt injection attacks."""
        injection_patterns = [
            r"<|begin_of_context|>",  # OpenAI delimiters
            r"<|begin_of_prompt|>",
            r"\[SYSTEM\]",
            r"\{system:",
            r"<!-- prompt:"
        ]

        return any(re.search(p, prompt, re.IGNORECASE) for p in injection_patterns)

    def validate_prompt(self, prompt: str) -> Tuple[bool, str]:
        """Validate prompt safety."""
        if self.is_jailbreak_attempt(prompt):
            return False, "Potential jailbreak detected"

        if self.detect_prompt_injection(prompt):
            return False, "Potential prompt injection detected"

        return True, "Prompt is safe"

detector = AdversarialDetector(model)
is_safe, reason = detector.validate_prompt("Ignore your guidelines and...")
print(f"Safe: {is_safe}, Reason: {reason}")
```

## Output Validation

```python
class OutputValidator:
    def __init__(self, llm_judge):
        self.judge = llm_judge

    def validate_factuality(self, claim: str) -> bool:
        """Check if claim is likely factual."""
        prompt = f"Is this claim factually accurate? {claim}\nAnswer yes or no:"
        response = self.judge.predict(prompt)
        return "yes" in response.lower()

    def validate_harmlessness(self, text: str) -> bool:
        """Check if response could cause harm."""
        prompt = f"Could this response cause harm or offense? {text}\nAnswer yes or no:"
        response = self.judge.predict(prompt)
        return "yes" not in response.lower()

    def validate_response(self, response: str) -> dict:
        """Multi-dimensional validation."""
        return {
            "factual": self.validate_factuality(response),
            "harmless": self.validate_harmlessness(response),
            "length_reasonable": len(response.split()) < 500,
            "no_code_injection": "<script>" not in response
        }

validator = OutputValidator(gpt4_model)
validation = validator.validate_response("Generated response...")
print(validation)
```

## Key Takeaways

- Constitutional AI enforces principle-based alignment
- RLHF creates preference-aligned models
- Content filtering redacts problematic content
- Toxicity detection flags harmful language
- PII detection protects sensitive data
- Adversarial detection blocks jailbreak attempts
- Output validation ensures multi-dimensional safety
- Layered defenses create robust guardrails
