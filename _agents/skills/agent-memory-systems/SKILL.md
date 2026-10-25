---
skill_name: agent-memory-systems
description: Agent memory: episodic, semantic, procedural, working memory, forgetting strategies
category: AI & LLM
version: 1.0.0
---

# Agent Memory Systems: Knowledge Retention & Recall

## Episodic Memory

```python
from datetime import datetime
from typing import List

class EpisodicMemory:
    """Store specific experiences with context."""

    def __init__(self, max_size: int = 1000):
        self.memories = []
        self.max_size = max_size

    def store(self, experience: str, outcome: str, timestamp: datetime = None):
        """Store a specific experience."""
        memory = {
            "experience": experience,
            "outcome": outcome,
            "timestamp": timestamp or datetime.now(),
            "relevance_score": 0.5
        }
        self.memories.append(memory)

        # Evict if full
        if len(self.memories) > self.max_size:
            self.memories.pop(0)

    def retrieve_similar(self, query: str, k: int = 5) -> List[dict]:
        """Retrieve similar past experiences."""
        from sklearn.feature_extraction.text import TfidfVectorizer

        vectorizer = TfidfVectorizer()
        experiences = [m["experience"] for m in self.memories]
        experiences.append(query)

        vectors = vectorizer.fit_transform(experiences)

        # Find most similar
        from sklearn.metrics.pairwise import cosine_similarity
        similarities = cosine_similarity([vectors[-1]], vectors[:-1])[0]

        top_indices = similarities.argsort()[-k:][::-1]
        return [self.memories[i] for i in top_indices]

episodic = EpisodicMemory()
episodic.store("Tried method A for task X", "Failed - too slow")
episodic.store("Tried method B for task X", "Succeeded - 2s runtime")

similar = episodic.retrieve_similar("How to solve task X quickly?")
```

## Semantic Memory

```python
class SemanticMemory:
    """Store facts and concepts."""

    def __init__(self):
        self.knowledge_base = {}

    def store_fact(self, subject: str, predicate: str, object: str):
        """Store a fact: subject-predicate-object."""
        if subject not in self.knowledge_base:
            self.knowledge_base[subject] = {}

        self.knowledge_base[subject][predicate] = object

    def query(self, subject: str, predicate: str) -> str:
        """Retrieve fact."""
        return self.knowledge_base.get(subject, {}).get(predicate)

    def infer(self, subject: str, target_predicate: str) -> str:
        """Infer unknown facts through rules."""
        # Simple rule: if A is_type X and X has property Y, then A has property Y
        type_pred = self.knowledge_base.get(subject, {}).get("is_type")
        if type_pred:
            return self.knowledge_base.get(type_pred, {}).get(target_predicate)
        return None

semantic = SemanticMemory()
semantic.store_fact("GPT-4", "is_type", "LLM")
semantic.store_fact("LLM", "capability", "token_generation")

capability = semantic.infer("GPT-4", "capability")  # Returns token_generation
```

## Procedural Memory

```python
class ProceduralMemory:
    """Store how to do things (skills/procedures)."""

    def __init__(self):
        self.procedures = {}

    def learn_procedure(self, name: str, steps: List[str], preconditions: List[str] = None):
        """Learn a procedure."""
        self.procedures[name] = {
            "steps": steps,
            "preconditions": preconditions or [],
            "success_rate": 0.5,
            "times_executed": 0
        }

    def can_execute(self, name: str, context: dict) -> bool:
        """Check if procedure can be executed in context."""
        if name not in self.procedures:
            return False

        proc = self.procedures[name]
        return all(context.get(cond) for cond in proc["preconditions"])

    def execute(self, name: str) -> List[str]:
        """Execute learned procedure."""
        if name not in self.procedures:
            raise ValueError(f"Unknown procedure: {name}")

        proc = self.procedures[name]
        proc["times_executed"] += 1
        return proc["steps"]

    def improve_procedure(self, name: str, success: bool):
        """Update success rate based on outcome."""
        proc = self.procedures[name]
        n = proc["times_executed"]
        # Bayesian update
        proc["success_rate"] = (proc["success_rate"] * n + (1.0 if success else 0)) / (n + 1)

procedural = ProceduralMemory()
procedural.learn_procedure(
    "web_search",
    ["Formulate query", "Search", "Parse results", "Return top 3"],
    preconditions=["internet_available"]
)

steps = procedural.execute("web_search")
procedural.improve_procedure("web_search", success=True)
```

## Working Memory

```python
class WorkingMemory:
    """Limited capacity, current focus."""

    def __init__(self, capacity: int = 5):
        self.capacity = capacity
        self.items = []

    def focus(self, item: str, priority: float = 0.5):
        """Add to working memory."""
        self.items.append({"content": item, "priority": priority})

        # Keep highest priority items
        if len(self.items) > self.capacity:
            self.items.sort(key=lambda x: x["priority"], reverse=True)
            self.items = self.items[:self.capacity]

    def get_context(self) -> str:
        """Get current working memory state."""
        return "\n".join([item["content"] for item in self.items])

    def clear(self):
        """Clear working memory."""
        self.items = []

working_memory = WorkingMemory(capacity=5)
working_memory.focus("Task: Write report", priority=0.9)
working_memory.focus("Constraint: 2000 words max", priority=0.8)

context = working_memory.get_context()
```

## Forgetting Strategies

```python
class MemoryWithForgetting:
    """Implement forgetting curves (Ebbinghaus)."""

    def __init__(self):
        self.memories = []

    def store(self, content: str):
        """Store with decay schedule."""
        import time
        self.memories.append({
            "content": content,
            "stored_at": time.time(),
            "accesses": 0,
            "last_accessed": time.time()
        })

    def retrieve(self, query: str) -> str:
        """Retrieve with decay consideration."""
        import time
        current_time = time.time()

        candidates = []
        for mem in self.memories:
            # Exponential decay: strength = initial_strength * exp(-decay_rate * age)
            age_seconds = current_time - mem["stored_at"]
            decay_rate = 0.1  # Per hour
            strength = 1.0 * (2.71828 ** (-decay_rate * age_seconds / 3600))

            # Boost by access frequency
            strength *= (1 + 0.1 * mem["accesses"])

            if strength > 0.1:  # Minimum strength threshold
                candidates.append((mem, strength))

        if not candidates:
            return None

        # Return strongest
        best = max(candidates, key=lambda x: x[1])[0]
        best["accesses"] += 1
        best["last_accessed"] = current_time
        return best["content"]

    def consolidate(self):
        """Remove weak memories during sleep."""
        self.memories = [
            m for m in self.memories
            if self._strength(m) > 0.2
        ]

    def _strength(self, memory: dict) -> float:
        import time
        age = time.time() - memory["stored_at"]
        return (2.71828 ** (-0.1 * age / 3600)) * (1 + 0.1 * memory["accesses"])

memory = MemoryWithForgetting()
memory.store("Important fact 1")
time.sleep(1)
memory.store("Important fact 2")

retrieved = memory.retrieve("fact")
memory.consolidate()
```

## Meta-Memory

```python
class MetaMemory:
    """Track memory quality and adjust strategies."""

    def __init__(self):
        self.memory_stats = {
            "total_stored": 0,
            "total_retrieved": 0,
            "successful_retrievals": 0,
            "false_positives": 0
        }

    def log_storage(self, category: str):
        self.memory_stats["total_stored"] += 1

    def log_retrieval(self, query: str, result: str, correct: bool):
        self.memory_stats["total_retrieved"] += 1
        if correct:
            self.memory_stats["successful_retrievals"] += 1

    def get_recall_accuracy(self) -> float:
        """Compute memory system accuracy."""
        if self.memory_stats["total_retrieved"] == 0:
            return 0.0

        return (
            self.memory_stats["successful_retrievals"] /
            self.memory_stats["total_retrieved"]
        )

    def recommend_strategy_changes(self) -> List[str]:
        """Recommend improvements."""
        accuracy = self.get_recall_accuracy()

        if accuracy < 0.5:
            return ["Increase encoding effort", "Use mnemonics", "More rehearsal"]
        elif accuracy < 0.8:
            return ["Improve retrieval cues", "Better organization"]
        else:
            return ["Current strategy effective"]

meta = MetaMemory()
meta.log_storage("facts")
meta.log_retrieval("fact query", "result", correct=True)
print(f"Accuracy: {meta.get_recall_accuracy():.2%}")
print(f"Recommendations: {meta.recommend_strategy_changes()}")
```

## Key Takeaways

- Episodic memory stores specific experiences
- Semantic memory holds facts and concepts
- Procedural memory captures skills
- Working memory maintains current focus
- Forgetting curves model memory decay
- Meta-memory tracks system performance
- Spaced repetition strengthens retention
