---
skill_name: ai-testing-patterns
description: Testing AI systems: determinism, prompt regression tests, golden datasets, CI evals
category: AI & LLM
version: 1.0.0
---

# Testing AI Systems: Quality Assurance

## Deterministic Testing

```python
def test_with_seed(seed: int = 42):
    """Test with fixed seed for reproducibility."""
    import random
    import numpy as np

    random.seed(seed)
    np.random.seed(seed)

    # LLM with temperature=0 is deterministic
    response = llm.predict("Question", temperature=0)
    assert "expected" in response.lower()

test_with_seed()
```

## Prompt Regression Tests

```python
import json

class PromptRegressionTest:
    def __init__(self, baseline_file: str = "prompt_baselines.json"):
        self.baseline_file = baseline_file
        self.baselines = self._load_baselines()

    def _load_baselines(self) -> dict:
        try:
            with open(self.baseline_file) as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def establish_baseline(self, prompt_name: str, prompt: str):
        """Create baseline."""
        response = llm.predict(prompt, temperature=0)
        self.baselines[prompt_name] = {
            "prompt": prompt,
            "response": response
        }
        self._save_baselines()

    def test_regression(self, prompt_name: str, prompt: str):
        """Check if response changed."""
        if prompt_name not in self.baselines:
            self.establish_baseline(prompt_name, prompt)
            return True

        baseline = self.baselines[prompt_name]
        current_response = llm.predict(prompt, temperature=0)

        # Exact match
        if baseline["response"] == current_response:
            return True

        # Semantic similarity threshold
        similarity = self._semantic_similarity(
            baseline["response"], current_response
        )

        return similarity > 0.95

    def _save_baselines(self):
        with open(self.baseline_file, "w") as f:
            json.dump(self.baselines, f, indent=2)

    def _semantic_similarity(self, text1: str, text2: str) -> float:
        from sentence_transformers import SentenceTransformer
        import numpy as np

        model = SentenceTransformer('all-MiniLM-L6-v2')
        emb1 = model.encode(text1)
        emb2 = model.encode(text2)

        return np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))

tester = PromptRegressionTest()
assert tester.test_regression("summarize", "Summarize this text...")
```

## Golden Dataset Testing

```python
class GoldenDatasetTest:
    def __init__(self, golden_file: str = "golden_dataset.json"):
        self.golden_file = golden_file
        self.dataset = self._load_dataset()

    def _load_dataset(self) -> list:
        with open(self.golden_file) as f:
            return json.load(f)

    def run_all_tests(self) -> dict:
        """Test against golden dataset."""
        results = {
            "passed": 0,
            "failed": 0,
            "details": []
        }

        for item in self.dataset:
            input_data = item["input"]
            expected = item["expected_output"]

            actual = llm.predict(input_data, temperature=0)

            if self._matches(actual, expected):
                results["passed"] += 1
            else:
                results["failed"] += 1
                results["details"].append({
                    "input": input_data,
                    "expected": expected,
                    "actual": actual
                })

        return results

    def _matches(self, actual: str, expected: str, threshold: float = 0.9) -> bool:
        """Check if output matches expected."""
        # Exact match
        if actual.strip() == expected.strip():
            return True

        # Semantic match
        from sentence_transformers import SentenceTransformer
        import numpy as np

        model = SentenceTransformer('all-MiniLM-L6-v2')
        sim = np.dot(
            model.encode(actual),
            model.encode(expected)
        ) / (np.linalg.norm(model.encode(actual)) * np.linalg.norm(model.encode(expected)))

        return sim > threshold

tester = GoldenDatasetTest()
results = tester.run_all_tests()
print(f"Passed: {results['passed']}, Failed: {results['failed']}")
```

## CI/CD Integration

```python
# pytest integration
import pytest

class TestAISystem:
    @pytest.mark.slow
    def test_summarization(self):
        """Test text summarization."""
        text = "Long document..."
        summary = llm.predict(f"Summarize: {text}")
        assert len(summary) < len(text)

    @pytest.mark.eval
    def test_qa_accuracy(self):
        """Test Q&A system."""
        qa_pairs = [
            ("What is AI?", "intelligence"),
            ("Define ML", "learning")
        ]

        for question, expected_keyword in qa_pairs:
            answer = llm.predict(question, temperature=0)
            assert expected_keyword.lower() in answer.lower()

    @pytest.mark.regression
    def test_prompt_regression(self):
        """Test for prompt drift."""
        tester = PromptRegressionTest()
        assert tester.test_regression("main_prompt", "Your prompt...")

# Run: pytest --mark eval
```

## Evaluation Metrics

```python
class AIMetrics:
    @staticmethod
    def exact_match(prediction: str, reference: str) -> float:
        return 1.0 if prediction.strip() == reference.strip() else 0.0

    @staticmethod
    def f1_score(prediction: str, reference: str) -> float:
        pred_tokens = set(prediction.lower().split())
        ref_tokens = set(reference.lower().split())

        if not pred_tokens or not ref_tokens:
            return 0.0

        overlap = pred_tokens & ref_tokens
        precision = len(overlap) / len(pred_tokens)
        recall = len(overlap) / len(ref_tokens)

        if precision + recall == 0:
            return 0.0

        return 2 * (precision * recall) / (precision + recall)

    @staticmethod
    def semantic_similarity(text1: str, text2: str) -> float:
        from sentence_transformers import SentenceTransformer
        import numpy as np

        model = SentenceTransformer('all-MiniLM-L6-v2')
        emb1 = model.encode(text1)
        emb2 = model.encode(text2)

        return float(np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2)))

# Test
metrics = AIMetrics()
assert metrics.semantic_similarity("Hello", "Hi") > 0.5
```

## Key Takeaways

- Temperature=0 ensures determinism
- Prompt regression detects changes
- Golden datasets validate correctness
- Semantic similarity measures quality
- CI/CD integration ensures quality gates
