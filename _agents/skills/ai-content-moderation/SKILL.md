---
skill_name: ai-content-moderation
description: Content moderation: classifier models, LLM-as-judge, human review workflow, audit
category: AI & LLM
version: 1.0.0
---

# Content Moderation: Automated & Human Review

## LLM-as-Judge

```python
class ContentModerator:
    def __init__(self, llm):
        self.llm = llm
        self.violation_categories = [
            "hate_speech",
            "violence",
            "sexual_content",
            "spam",
            "misinformation"
        ]

    def moderate(self, text: str) -> dict:
        """Moderate content using LLM."""
        prompt = f"""
Review this content for violations:
{text}

Categories to check: {', '.join(self.violation_categories)}

For each category, provide:
1. Violates? (yes/no)
2. Severity (0-10)
3. Confidence (0-1)

Return JSON format.
"""
        response = self.llm.predict(prompt)
        return json.loads(response)

    def should_remove(self, text: str, severity_threshold: float = 7.0) -> bool:
        """Decide if content should be removed."""
        moderation = self.moderate(text)

        for category, judgment in moderation.items():
            if (judgment.get("violates") and
                judgment.get("severity", 0) >= severity_threshold):
                return True

        return False

moderator = ContentModerator(llm)
moderation = moderator.moderate("Some user text...")

if moderator.should_remove("Some text"):
    print("Content flagged for removal")
```

## Classifier-Based Moderation

```python
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC

class TrainedModerator:
    def __init__(self):
        self.pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(max_features=10000)),
            ("classifier", LinearSVC())
        ])

        self.trained = False

    def train(self, texts: list[str], labels: list[int]):
        """Train on labeled data."""
        self.pipeline.fit(texts, labels)
        self.trained = True

    def moderate(self, text: str) -> dict:
        """Classify and return judgment."""
        if not self.trained:
            raise ValueError("Model not trained")

        prediction = self.pipeline.predict([text])[0]
        confidence = max(self.pipeline.predict_proba([text])[0])

        return {
            "is_violation": prediction == 1,
            "confidence": confidence
        }

moderator = TrainedModerator()

# Train on labeled dataset
texts = ["clean content", "offensive content"]
labels = [0, 1]
moderator.train(texts, labels)

# Predict on new content
result = moderator.moderate("new text")
```

## Human Review Workflow

```python
from dataclasses import dataclass
from enum import Enum

class ReviewStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"

@dataclass
class ModerationCase:
    id: str
    content: str
    auto_decision: str
    auto_confidence: float
    human_review: str = None
    reviewer: str = None
    status: ReviewStatus = ReviewStatus.PENDING

class ModerationQueue:
    def __init__(self):
        self.queue = []
        self.reviewed = []

    def add_case(self, case: ModerationCase):
        """Add to review queue."""
        if case.auto_confidence < 0.7:  # Low confidence → escalate
            case.status = ReviewStatus.ESCALATED
        self.queue.append(case)

    def get_next_case(self) -> ModerationCase:
        """Get next case for human review."""
        # Prioritize escalated cases
        for case in self.queue:
            if case.status == ReviewStatus.ESCALATED:
                return case

        return self.queue[0] if self.queue else None

    def submit_review(self, case_id: str, decision: str, reviewer: str):
        """Submit human review."""
        case = next((c for c in self.queue if c.id == case_id), None)
        if case:
            case.human_review = decision
            case.reviewer = reviewer
            case.status = ReviewStatus.APPROVED if decision == "approve" else ReviewStatus.REJECTED
            self.queue.remove(case)
            self.reviewed.append(case)

    def get_audit_log(self) -> list:
        """Get moderation history for audit."""
        return self.reviewed

queue = ModerationQueue()

# Auto-moderation
moderator = ContentModerator(llm)
result = moderator.moderate("text")
case = ModerationCase(
    id="case1",
    content="text",
    auto_decision=result.get("decision"),
    auto_confidence=result.get("confidence", 0.5)
)
queue.add_case(case)

# Human review
next_case = queue.get_next_case()
queue.submit_review("case1", "approve", "reviewer@example.com")

# Audit
audit = queue.get_audit_log()
```

## Appeal Process

```python
class AppealHandler:
    def __init__(self, llm):
        self.llm = llm
        self.appeals = []

    def submit_appeal(self, case_id: str, appeal_text: str) -> str:
        """Submit appeal of moderation decision."""
        self.appeals.append({
            "case_id": case_id,
            "appeal_text": appeal_text,
            "status": "pending"
        })

        return f"Appeal {case_id} submitted for review"

    def review_appeal(self, case_id: str) -> dict:
        """Review appeal using LLM."""
        appeal = next((a for a in self.appeals if a["case_id"] == case_id), None)

        if not appeal:
            return None

        prompt = f"""
Original moderation decision: remove
Appeal: {appeal['appeal_text']}

Should the decision be overturned? (yes/no)
Reasoning:
"""
        response = self.llm.predict(prompt)

        return {
            "case_id": case_id,
            "overturn": "yes" in response.lower(),
            "reasoning": response
        }

handler = AppealHandler(llm)
handler.submit_appeal("case1", "I disagree with the decision")
review = handler.review_appeal("case1")
```

## Key Takeaways

- LLM-as-judge handles nuanced judgments
- Classifiers provide fast decisions
- Human review ensures accuracy
- Escalation handles uncertain cases
- Appeals enable reconsideration
- Audit logs track decisions
