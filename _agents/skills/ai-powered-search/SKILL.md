---
skill_name: ai-powered-search
description: AI search: hybrid search, reranking, query expansion, conversational search UI
category: AI & LLM
version: 1.0.0
---

# AI-Powered Search: Advanced Retrieval Patterns

## Hybrid Search

```python
from langchain.vectorstores import Chroma
from langchain.retrievers import BM25Retriever, EnsembleRetriever
from langchain.embeddings import OpenAIEmbeddings

# Dense retrieval (semantic)
embeddings = OpenAIEmbeddings()
vectorstore = Chroma.from_documents(documents, embeddings)
dense_retriever = vectorstore.as_retriever(k=10)

# Sparse retrieval (keyword)
sparse_retriever = BM25Retriever.from_documents(documents)
sparse_retriever.k = 10

# Ensemble (hybrid)
ensemble = EnsembleRetriever(
    retrievers=[dense_retriever, sparse_retriever],
    weights=[0.6, 0.4]  # 60% semantic, 40% keyword
)

# Query
results = ensemble.get_relevant_documents("Best practices for AI deployment")
# Combines semantic understanding with keyword matching
```

## Reranking

```python
from langchain.document_compressors import CohereRerank
from langchain.retrievers import ContextualCompressionRetriever

# Initial retrieval (wide net)
base_retriever = vectorstore.as_retriever(k=20)

# Reranker improves quality
reranker = CohereRerank(top_n=5)
compression_retriever = ContextualCompressionRetriever(
    base_compressor=reranker,
    base_retriever=base_retriever
)

# Get top-5 reranked from initial 20
results = compression_retriever.get_relevant_documents("Your query")

# Custom reranking with LLM
class LLMReranker:
    def rerank(self, query: str, documents: list) -> list:
        """Rerank using LLM judgment."""
        scores = []

        for doc in documents:
            prompt = f"""
Query: {query}
Document: {doc.page_content}

Relevance (0-10):
"""
            score = float(llm.predict(prompt))
            scores.append(score)

        # Sort by score
        ranked = sorted(zip(documents, scores), key=lambda x: x[1], reverse=True)
        return [doc for doc, score in ranked]
```

## Query Expansion

```python
from langchain.chains import MultiQueryRetriever

# Multi-query expansion
retriever = vectorstore.as_retriever()

multi_query_retriever = MultiQueryRetriever.from_llm(
    retriever=retriever,
    llm=ChatOpenAI(temperature=0),
    prompt=PromptTemplate(
        template="""Generate 3 alternative phrasings of this question:
{question}

Alternate phrasings:""",
        input_variables=["question"]
    )
)

# Retrieves from multiple query perspectives
docs = multi_query_retriever.get_relevant_documents("Machine learning basics")

# Custom expansion
def expand_query(query: str) -> list[str]:
    """Expand query programmatically."""
    expansions = [
        query,  # Original
        f"Explain {query}",  # Expanded
        f"How to {query}",  # Alternative
        f"Benefits of {query}"  # Alternative
    ]
    return expansions

expanded = expand_query("deep learning")
# Search with all variants
```

## Conversational Search

```python
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain

# With memory
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

qa_chain = ConversationalRetrievalChain.from_llm(
    llm=ChatOpenAI(model="gpt-4"),
    retriever=ensemble,
    memory=memory,
    return_source_documents=True,
    verbose=True
)

# Multi-turn conversation
response1 = qa_chain({"question": "What is machine learning?"})
response2 = qa_chain({"question": "Can you give examples?"})  # Remembers context

# Custom conversational search
class ConversationalSearch:
    def __init__(self, retriever, llm):
        self.retriever = retriever
        self.llm = llm
        self.history = []

    def search(self, query: str) -> str:
        # Add to history
        self.history.append({"query": query})

        # Retrieve documents
        docs = self.retriever.get_relevant_documents(query)

        # Generate answer with context
        context = "\n".join([doc.page_content for doc in docs])
        prompt = f"""
Search history: {self.history[-3:]}
Current query: {query}
Retrieved context: {context}

Answer:
"""
        answer = self.llm.predict(prompt)
        self.history.append({"answer": answer})
        return answer

search = ConversationalSearch(ensemble, ChatOpenAI())
```

## Federated Search

```python
class FederatedSearch:
    """Search across multiple sources."""

    def __init__(self, sources: dict):
        self.sources = sources

    def search(self, query: str) -> dict:
        """Search all sources and merge results."""
        results = {}

        for source_name, retriever in self.sources.items():
            docs = retriever.get_relevant_documents(query)
            results[source_name] = docs[:3]  # Top 3 from each

        # Merge and deduplicate
        merged = self._merge_results(results)
        return merged

    def _merge_results(self, results: dict) -> list:
        """Merge results from multiple sources."""
        seen = set()
        merged = []

        for source, docs in results.items():
            for doc in docs:
                # Deduplicate by content
                if doc.page_content not in seen:
                    merged.append({"source": source, "doc": doc})
                    seen.add(doc.page_content)

        return merged

# Use federated search
federated = FederatedSearch({
    "web": web_retriever,
    "docs": doc_retriever,
    "kb": kb_retriever
})

results = federated.search("Python best practices")
```

## Key Takeaways

- Hybrid search combines dense and sparse retrieval
- Reranking improves relevance of initial results
- Query expansion captures different phrasings
- Conversational search maintains context
- Federated search queries multiple sources
- Ensemble approaches leverage different strengths
