---
skill_name: ai-summarization
description: Summarization: extractive vs abstractive, hierarchical, query-focused, evaluation
category: AI & LLM
version: 1.0.0
---

# Text Summarization

## Abstractive Summarization

```python
class AbstractiveSummarizer:
    def __init__(self, llm):
        self.llm = llm

    def summarize(self, text: str, max_sentences: int = 3) -> str:
        """Generate abstractive summary."""
        prompt = f"""
Summarize in {max_sentences} sentences:

{text}

Summary:
"""
        return self.llm.predict(prompt)

    def query_focused_summary(self, text: str, query: str) -> str:
        """Summarize focusing on specific query."""
        prompt = f"""
Text:
{text}

Query: {query}

Summarize the text answering the query in 2-3 sentences.
"""
        return self.llm.predict(prompt)

summarizer = AbstractiveSummarizer(llm)
summary = summarizer.summarize(long_article)
```

## Extractive Summarization

```python
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class ExtractiveSummarizer:
    def summarize(self, text: str, num_sentences: int = 3) -> str:
        """Extract top sentences."""
        sentences = text.split(".")
        sentences = [s.strip() for s in sentences if s.strip()]

        if len(sentences) <= num_sentences:
            return text

        # Vectorize
        vectorizer = TfidfVectorizer()
        tfidf = vectorizer.fit_transform(sentences)

        # Score sentences
        scores = np.array(tfidf.sum(axis=1)).flatten()

        # Select top
        top_indices = np.argsort(-scores)[:num_sentences]
        top_indices = sorted(top_indices)

        summary = ". ".join([sentences[i] for i in top_indices])
        return summary + "."

summarizer = ExtractiveSummarizer()
summary = summarizer.summarize(text)
```

## Hierarchical Summarization

```python
class HierarchicalSummarizer:
    def __init__(self, llm):
        self.llm = llm

    def summarize_hierarchical(self, text: str, max_summary_length: int = 200) -> str:
        """Hierarchical abstraction."""
        # Level 1: Summarize paragraphs
        paragraphs = text.split("\n\n")
        para_summaries = []

        for para in paragraphs:
            summary = self.llm.predict(f"Summarize in 1 sentence:\n{para}")
            para_summaries.append(summary)

        # Level 2: Summarize paragraph summaries
        combined = "\n".join(para_summaries)
        final = self.llm.predict(f"Summarize in 3 sentences:\n{combined}")

        return final

summarizer = HierarchicalSummarizer(llm)
```

## Multi-Document Summarization

```python
class MultiDocumentSummarizer:
    def __init__(self, llm):
        self.llm = llm

    def summarize_documents(self, documents: list[str]) -> str:
        """Summarize across multiple documents."""
        combined = "\n---\n".join(documents)

        prompt = f"""
Summarize common themes from these documents:

{combined}

Key themes:
"""
        return self.llm.predict(prompt)

summarizer = MultiDocumentSummarizer(llm)
result = summarizer.summarize_documents([doc1, doc2, doc3])
```

## Evaluation

```python
class SummarizationEvaluator:
    @staticmethod
    def rouge_score(summary: str, reference: str) -> dict:
        """ROUGE evaluation."""
        from rouge import Rouge

        rouge = Rouge()
        scores = rouge.get_scores(summary, reference)[0]

        return {
            "rouge1": scores["rouge1"]["f"],
            "rouge2": scores["rouge2"]["f"],
            "rougeL": scores["rougeL"]["f"]
        }

    @staticmethod
    def length_ratio(summary: str, original: str) -> float:
        """Compression ratio."""
        return len(summary.split()) / len(original.split())

    @staticmethod
    def evaluate_coherence(summary: str, llm) -> float:
        """LLM judges coherence."""
        prompt = f"Rate coherence 0-10:\n{summary}\nScore:"
        score = float(llm.predict(prompt))
        return score / 10.0

evaluator = SummarizationEvaluator()

rouge = evaluator.rouge_score(generated_summary, reference_summary)
ratio = evaluator.length_ratio(generated_summary, original)
coherence = evaluator.evaluate_coherence(generated_summary, llm)
```

## Key Takeaways

- Abstractive summarization generates new sentences
- Extractive summarization selects existing sentences
- Hierarchical approach works for long documents
- Multi-document summarization finds common themes
- ROUGE metrics evaluate quality
