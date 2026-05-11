# LibraryMind — Part 4: RAG Engine Architecture

---

## What is RAG?

A regular AI model like ChatGPT only knows what it learned during training. If you ask it *"What books about robots do we have in our library?"*, it will either make something up (called **hallucination**) or say it doesn't know.

**RAG (Retrieval-Augmented Generation)** solves this by splitting the job into two steps:

1. **Retrieve** — First, search your own database for real, relevant information.
2. **Generate** — Then, hand that real information to the AI and say *"Only answer based on THIS. Cite your sources."*

The result is an AI that answers questions about **your specific data** accurately and honestly, without inventing facts.

---

## The Mermaid Architecture Diagram

```mermaid
flowchart TB
    classDef user fill:#e8d5f5,stroke:#7b2d8b,stroke-width:2px
    classDef api fill:#d5e8f5,stroke:#1a6b9e,stroke-width:2px
    classDef rag fill:#fff3cd,stroke:#b8860b,stroke-width:2px
    classDef shared fill:#d5f5e3,stroke:#1a7a42,stroke-width:2px
    classDef knowledge fill:#fde8d5,stroke:#9e4a1a,stroke-width:2px
    classDef providers fill:#f5d5d5,stroke:#9e1a1a,stroke-width:2px
    classDef output fill:#d5f5f5,stroke:#1a7a7a,stroke-width:2px

    %% ── Layer 1: User ──────────────────────────────────────────────
    subgraph CLIENT["👤 User / Client"]
        patron["Patron / End User"]
        ui["Swagger UI / Postman / Frontend"]
        patron --> ui
    end

    %% ── Layer 2: API ───────────────────────────────────────────────
    subgraph API["⚡ API Layer (FastAPI)"]
        endpoint["POST /search/ask"]
        validate["Request Validation\n(Pydantic Model)"]
        formatter["JSON Response Formatter"]
        endpoint --> validate
    end

    %% ── Layer 3: RAG Engine ────────────────────────────────────────
    subgraph RAG["🧠 RAG Engine"]
        direction TB
        cache_check{"Cache\nCheck"}
        rate_check{"Rate Limit\nCheck"}
        query_embed["Query Embedding\n(turn question into vector)"]
        vec_search["Vector Search\n(search ChromaDB)"]
        threshold{"Relevance\nThreshold Filter\n≥ 0.7?"}
        ctx_builder["Context Builder\n(format top-K books)"]
        prompt_builder["Prompt Builder\n(add instructions + context)"]
        response_parser["Response Parser\n(extract clean answer)"]
        cache_store["Cache Final Response"]

        cache_check -->|"✅ Cache HIT"| cache_store
        cache_check -->|"❌ Cache MISS"| rate_check
        rate_check -->|"🚫 Limit Exceeded"| formatter
        rate_check -->|"✅ Allowed"| query_embed
        query_embed --> vec_search
        vec_search --> threshold
        threshold -->|"❌ No relevant results"| formatter
        threshold -->|"✅ Grounded Prompt"| ctx_builder
        ctx_builder --> prompt_builder
        prompt_builder --> response_parser
        response_parser --> cache_store
        cache_store --> formatter
    end

    %% ── Layer 4: Shared Services ───────────────────────────────────
    subgraph SHARED["🔧 Shared Services"]
        embed_svc["Embedding Service\n(text → vector)"]
        cache_svc["Cache Service\n(Redis, optional)"]
        usage_tracker["Usage Tracker\n(tokens + cost)"]
    end

    %% ── Layer 5: Knowledge Base ────────────────────────────────────
    subgraph KNOWLEDGE["📚 Knowledge Base"]
        chroma["ChromaDB\nVector Store"]
        embeddings["Stored Book\nEmbeddings"]
        metadata["Book Metadata\n(title, author, genre)"]
        books_json["books.json\n(original source data)"]
        books_json -.->|"Seeded Once"| chroma
        chroma --- embeddings
        chroma --- metadata
    end

    %% ── Layer 6: AI Providers ──────────────────────────────────────
    subgraph PROVIDERS["🤖 AI Provider Layer"]
        resilient["ResilientAIService"]
        retry["Retry Logic"]
        fallback["Fallback Logic"]
        openai_p["OpenAI Provider"]
        claude_p["Claude Provider"]
        gemini_p["Gemini Provider"]

        resilient --> retry
        retry --> openai_p
        openai_p -->|"Fails → Fallback"| fallback
        fallback --> claude_p
        claude_p -->|"Fails → Fallback"| gemini_p
    end

    %% ── Layer 7: Output ────────────────────────────────────────────
    subgraph OUTPUT["📤 Output"]
        answer["Answer Text"]
        sources["Source Books Cited"]
        scores["Relevance Scores"]
        cached_flag["cached: true/false"]
    end

    %% ── Main Flow ──────────────────────────────────────────────────
    ui -->|"User question (JSON)"| endpoint
    validate --> cache_check

    %% RAG ↔ Shared Services
    cache_check <-->|"Read / Write"| cache_svc
    cache_store <-->|"Store result"| cache_svc
    query_embed <-->|"Generate embedding"| embed_svc
    response_parser -->|"Record tokens + cost\n(only on real AI call)"| usage_tracker

    %% RAG ↔ Knowledge Base
    vec_search <-->|"Query top-K vectors"| chroma
    embed_svc <-->|"Embed query"| chroma

    %% RAG ↔ AI Providers
    prompt_builder -->|"Send grounded prompt"| resilient
    resilient -->|"AI response"| response_parser

    %% Output
    formatter --> answer & sources & scores & cached_flag

    %% Styles
    class patron,ui user
    class endpoint,validate,formatter api
    class cache_check,rate_check,query_embed,vec_search,threshold,ctx_builder,prompt_builder,response_parser,cache_store rag
    class embed_svc,cache_svc,usage_tracker shared
    class chroma,embeddings,metadata,books_json knowledge
    class resilient,retry,fallback,openai_p,claude_p,gemini_p providers
    class answer,sources,scores,cached_flag output
```

---

## Request Flow: Step by Step

This is the exact journey a single question takes through the system.

| Step | What Happens | Component |
|------|-------------|-----------|
| 1 | User sends: `POST /search/ask` with `{ "question": "I want a sci-fi book about space survival" }` | Client |
| 2 | FastAPI validates the JSON shape (correct fields, types, limits) | Request Validation |
| 3 | Cache is checked: Has this exact question been asked before? | Cache Service (Redis) |
| 4 | **If Cache HIT** → return the saved answer immediately. No AI call needed. | Cache Service |
| 5 | **If Cache MISS** → check if the user is within their rate limit | Rate Limiter |
| 6 | The user's question is converted into a vector (list of numbers) | Embedding Service |
| 7 | That vector is compared against all 20 book vectors in ChromaDB | Vector Store |
| 8 | Top-K results are returned with similarity scores (e.g., 0.87, 0.74, 0.61) | Vector Store |
| 9 | **If all scores < 0.7** → return `"I couldn't find a relevant book."` No hallucination. | Threshold Filter |
| 10 | **If scores ≥ 0.7** → format those books into a readable "context block" | Context Builder |
| 11 | A prompt is built: `"You are a librarian. Answer ONLY from these books: [context]. Cite the title."` | Prompt Builder |
| 12 | The prompt is sent to `ResilientAIService`. It tries OpenAI first, then Claude, then Gemini | AI Provider Layer |
| 13 | The AI writes an answer. Tokens used and cost are recorded | Usage Tracker |
| 14 | The raw AI text is parsed into a clean structured object | Response Parser |
| 15 | The final response is saved in Redis for future identical questions | Cache Service |
| 16 | The user receives a JSON response with `answer`, `sources`, `scores`, `cached: false` | Output |

---

## Key Branches Explained

### ✅ Cache HIT
> The exact same question was asked before. Redis returns the stored answer in milliseconds. The AI is never called. No cost, no latency.

### ❌ Cache MISS
> The question is new. The full RAG pipeline runs. At the end, the answer is saved so the next identical question gets a Cache HIT.

### 🚫 Rate Limit Exceeded
> The user has made too many requests in the last minute. The Token Bucket is empty. The request is rejected with a `429 Too Many Requests` error before any expensive computation begins.

### ❌ No Relevant Results (Below Threshold)
> The best matching book scored below `0.7` (configured in `.env` as `RAG_RELEVANCE_THRESHOLD`). Instead of making up an answer, the system honestly responds: *"I couldn't find a book relevant to your question."* This prevents hallucination.

### ✅ Grounded Prompt
> At least one book cleared the relevance threshold. The AI is instructed to answer **only** from that context. It cannot invent facts. It must cite the book it used.

### 🔁 Provider Fallback
> If OpenAI is down or over quota (like we saw during testing), `ResilientAIService` catches the error and automatically retries with Claude, then Gemini. The user never sees the failure.

---

## What the Final Answer Looks Like

```json
{
  "answer": "Based on your interest in space survival, I recommend 'The Martian' by Andy Weir. It follows an astronaut stranded on Mars who must use science and ingenuity to survive...",
  "sources": [
    {
      "title": "The Martian",
      "author": "Andy Weir",
      "genre": "Science Fiction",
      "score": 0.91
    }
  ],
  "relevance_scores": [0.91, 0.78],
  "cached": false
}
```

> **`cached: false`** means this was a real AI call. If you ask the same question again, `cached: true` will appear and the response will be instant.
