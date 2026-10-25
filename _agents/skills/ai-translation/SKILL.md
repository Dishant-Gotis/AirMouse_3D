---
skill_name: ai-translation
description: AI translation: LLM-based, glossary injection, quality estimation, BLEU scores
category: AI & LLM
version: 1.0.0
---

# Machine Translation with AI

## LLM-Based Translation

```python
class TranslationEngine:
    def __init__(self, llm):
        self.llm = llm

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translate text."""
        prompt = f"""
Translate from {source_lang} to {target_lang}:

{text}

Translation:
"""
        return self.llm.predict(prompt)

    def batch_translate(self, texts: list[str], target_lang: str) -> list[str]:
        """Translate multiple texts."""
        results = []
        for text in texts:
            translated = self.translate(text, "auto", target_lang)
            results.append(translated)
        return results

engine = TranslationEngine(llm)

result = engine.translate("Hello, how are you?", "en", "es")
print(result)  # "Hola, ¿cómo estás?"
```

## Glossary Injection

```python
class GlossaryTranslator:
    def __init__(self, llm):
        self.llm = llm
        self.glossary = {}

    def add_term(self, source_term: str, target_term: str):
        """Add term to glossary."""
        self.glossary[source_term] = target_term

    def translate_with_glossary(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translate respecting glossary."""
        # Build glossary string
        glossary_str = "\n".join([
            f"{source} → {target}"
            for source, target in self.glossary.items()
        ])

        prompt = f"""
Use this glossary:
{glossary_str}

Translate from {source_lang} to {target_lang}, using glossary terms:
{text}

Translation:
"""
        return self.llm.predict(prompt)

translator = GlossaryTranslator(llm)
translator.add_term("AI", "IA")
translator.add_term("machine learning", "aprendizaje automático")

result = translator.translate_with_glossary(
    "AI and machine learning are important",
    "en", "es"
)
```

## Quality Estimation

```python
class TranslationQualityEstimator:
    def __init__(self, llm):
        self.llm = llm

    def estimate_quality(self, source: str, translation: str) -> dict:
        """Estimate translation quality."""
        prompt = f"""
Source: {source}
Translation: {translation}

Evaluate translation quality on:
1. Accuracy (0-10)
2. Fluency (0-10)
3. Completeness (0-10)

Return JSON format.
"""
        response = self.llm.predict(prompt)
        return json.loads(response)

    def needs_review(self, source: str, translation: str, threshold: float = 7.0) -> bool:
        """Check if translation needs human review."""
        quality = self.estimate_quality(source, translation)
        avg_score = sum(quality.values()) / len(quality)
        return avg_score < threshold

estimator = TranslationQualityEstimator(llm)

quality = estimator.estimate_quality("Hello", "Bonjour")
if estimator.needs_review("Hello", "Bonjour"):
    print("Needs review")
```

## BLEU Score Evaluation

```python
class TranslationEvaluator:
    @staticmethod
    def bleu_score(reference: str, hypothesis: str) -> float:
        """Calculate BLEU score."""
        from nltk.translate.bleu_score import sentence_bleu
        from nltk.tokenize import word_tokenize

        ref_tokens = word_tokenize(reference)
        hyp_tokens = word_tokenize(hypothesis)

        return sentence_bleu([ref_tokens], hyp_tokens)

    @staticmethod
    def meteor_score(reference: str, hypothesis: str) -> float:
        """METEOR evaluation (more lenient than BLEU)."""
        from nltk.translate.meteor_score import meteor_score

        return meteor_score([reference], hypothesis)

evaluator = TranslationEvaluator()

reference = "The quick brown fox"
hypothesis = "The fast brown fox"

bleu = evaluator.bleu_score(reference, hypothesis)
meteor = evaluator.meteor_score(reference, hypothesis)

print(f"BLEU: {bleu:.3f}, METEOR: {meteor:.3f}")
```

## Key Takeaways

- LLM translation is fast and natural
- Glossaries ensure terminology consistency
- Quality estimation flags problematic translations
- BLEU and METEOR provide automated evaluation
- Human review catches nuanced errors
