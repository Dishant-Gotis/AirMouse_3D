---
skill_name: ai-classification
description: Classification: zero-shot, few-shot, fine-tuned classifiers, routing agents
category: AI & LLM
version: 1.0.0
---

# Text Classification

## Zero-Shot Classification

```python
from transformers import pipeline

class ZeroShotClassifier:
    def __init__(self):
        self.classifier = pipeline("zero-shot-classification",
                                   model="facebook/bart-large-mnli")

    def classify(self, text: str, labels: list[str]) -> dict:
        """Classify without training."""
        result = self.classifier(text, labels)

        return {
            "text": text,
            "scores": dict(zip(result["labels"], result["scores"])),
            "top_label": result["labels"][0]
        }

classifier = ZeroShotClassifier()

result = classifier.classify(
    "This product is amazing!",
    ["positive", "negative", "neutral"]
)
# {"top_label": "positive", "scores": {...}}
```

## Few-Shot Classification

```python
class FewShotClassifier:
    def __init__(self, llm):
        self.llm = llm

    def classify_with_examples(self, text: str, examples: list[dict], labels: list[str]) -> str:
        """Classify with examples."""
        examples_str = "\n".join([
            f"Text: {ex['text']}\nClass: {ex['label']}"
            for ex in examples
        ])

        prompt = f"""
Examples:
{examples_str}

Classify this text as one of: {', '.join(labels)}
Text: {text}

Class:
"""
        return self.llm.predict(prompt)

classifier = FewShotClassifier(llm)

examples = [
    {"text": "Great product!", "label": "positive"},
    {"text": "Terrible experience", "label": "negative"}
]

result = classifier.classify_with_examples(
    "Amazing quality!",
    examples,
    ["positive", "negative"]
)
```

## Fine-Tuned Classification

```python
from transformers import AutoModelForSequenceClassification, AutoTokenizer, Trainer, TrainingArguments
from datasets import Dataset

class FineTunedClassifier:
    def __init__(self, model_name: str = "distilbert-base-uncased"):
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)

    def train(self, texts: list[str], labels: list[int]):
        """Fine-tune classifier."""
        dataset = Dataset.from_dict({
            "text": texts,
            "label": labels
        })

        def tokenize_fn(batch):
            return self.tokenizer(batch["text"], truncation=True)

        tokenized = dataset.map(tokenize_fn, batched=True)

        args = TrainingArguments(
            output_dir="./results",
            num_train_epochs=3,
            per_device_train_batch_size=8
        )

        trainer = Trainer(
            model=self.model,
            args=args,
            train_dataset=tokenized
        )

        trainer.train()

    def classify(self, text: str) -> dict:
        """Classify with fine-tuned model."""
        inputs = self.tokenizer(text, return_tensors="pt")
        outputs = self.model(**inputs)
        logits = outputs.logits
        predicted_class = logits.argmax().item()

        return {"label": predicted_class}

classifier = FineTunedClassifier()
classifier.train(["positive text"] * 10, [1] * 10)
```

## Routing Classification

```python
class RoutingClassifier:
    def __init__(self, llm):
        self.llm = llm
        self.routers = {}

    def register_router(self, class_name: str, handler):
        """Register handler for class."""
        self.routers[class_name] = handler

    def classify_and_route(self, text: str, classes: list[str]):
        """Classify and route to handler."""
        # Classify
        prompt = f"""
Classify as one of: {', '.join(classes)}
Text: {text}

Class:
"""
        predicted_class = self.llm.predict(prompt).strip().lower()

        # Route
        handler = self.routers.get(predicted_class)
        if handler:
            return handler(text)

        return f"No handler for {predicted_class}"

router = RoutingClassifier(llm)

router.register_router("question", lambda x: f"Answer to: {x}")
router.register_router("statement", lambda x: f"Acknowledge: {x}")

result = router.classify_and_route("What is AI?", ["question", "statement"])
```

## Key Takeaways

- Zero-shot works without training
- Few-shot uses examples
- Fine-tuning maximizes accuracy
- Routing directs to specialized handlers
- Ensemble combines multiple classifiers
