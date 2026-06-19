# LibraryMind — System Architecture

> Full system overview including all services, infrastructure, and the final intent-routing layer added to the chat service.

---

## High-Level Architecture

```mermaid
flowchart TB
    classDef client   fill:#e0f0ff,stroke:#3399ff,stroke-width:2px
    classDef api      fill:#fff0cc,stroke:#ffaa00,stroke-width:2px
    classDef service  fill:#e8f5e9,stroke:#4caf50,stroke-width:2px
    classDef infra    fill:#fce4ec,stroke:#e91e63,stroke-width:2px
    classDef storage  fill:#f3e5f5,stroke:#9c27b0,stroke-width:2px
    classDef ai       fill:#e3f2fd,stroke:#1976d2,stroke-width:2px

    PATRON["👤 Patron / Client"]:::client

    subgraph API["API Layer · FastAPI"]
        direction LR
        CHAT_R["POST /chat"]:::api
        ASK_R["POST /search/ask"]:::api
        BOOKS_R["POST /search/books"]:::api
        CLASS_R["POST /classify"]:::api
        SUM_R["POST /summarise"]:::api
        HEALTH["GET /health"]:::api
    end

    subgraph SERVICES["Service Layer"]
        CHAT_SVC["ChatService\n• Intent Router\n• Conversation Memory\n• Prompt Builder"]:::service
        RAG_SVC["RAGService\n• Embed → Search → Filter\n• Cache Check\n• Grounded Answer"]:::service
        EMB_SVC["EmbeddingService\n• Text → Vector"]:::service
        CLASS_SVC["ClassificationService\n• Ticket → JSON"]:::service
        SUM_SVC["SummarisationService\n• Book → Summary"]:::service
    end

    subgraph INTENT["Intent Routing (Chat Only)"]
        direction LR
        CLASSIFY["_classify_intent()"]:::service
        CAT["catalogue_lookup\n→ try RAG"]:::service
        BOOK["book_knowledge\n→ try RAG first\nthen AI general"]:::service
        GEN["general\n→ skip RAG\npolite redirect"]:::service
        CLASSIFY --> CAT & BOOK & GEN
    end

    subgraph INFRA["Infrastructure Layer"]
        direction LR
        CACHE["Cache\n(Redis / In-memory)"]:::infra
        LIMITER["Rate Limiter\n(Token Bucket)"]:::infra
        USAGE["Usage Tracker\n(tokens + cost)"]:::infra
        CONV_STORE["ConversationStore\n(per-session history)"]:::infra
    end

    subgraph STORAGE["Storage Layer"]
        CHROMA["ChromaDB\n(Vector Store)"]:::storage
        BOOKS_JSON["books.json\n(Catalogue Source)"]:::storage
        SEED["seed_books.py"]:::storage
        BOOKS_JSON --> SEED --> CHROMA
    end

    subgraph PROVIDERS["AI Provider Layer · ResilientAIService"]
        direction LR
        OPENAI["🟢 OpenAI\n(primary)"]:::ai
        CLAUDE["🟡 Claude\n(fallback 1)"]:::ai
        GEMINI["🔵 Gemini\n(fallback 2)"]:::ai
        OPENAI -..->|"fails"| CLAUDE -..->|"fails"| GEMINI
    end

    %% Client to API
    PATRON -->|"HTTP request"| API

    %% API to Services
    CHAT_R --> CHAT_SVC
    ASK_R  --> RAG_SVC
    BOOKS_R --> EMB_SVC
    CLASS_R --> CLASS_SVC
    SUM_R  --> SUM_SVC

    %% Chat Service → Intent Router
    CHAT_SVC --> INTENT
    CAT & BOOK -->|"call RAG"| RAG_SVC

    %% RAG pipeline
    RAG_SVC --> EMB_SVC --> CHROMA
    RAG_SVC <--> CACHE

    %% Services → AI Providers
    RAG_SVC & CHAT_SVC & CLASS_SVC & SUM_SVC & CLASSIFY --> PROVIDERS

    %% Infrastructure wiring
    CHAT_SVC <-->|"read/write history"| CONV_STORE
    RAG_SVC & CHAT_SVC --> LIMITER
    RAG_SVC & CHAT_SVC & CLASS_SVC & SUM_SVC --> USAGE
```

---

## Component Breakdown

### Configuration (`app/config.py`)
Loads and validates all settings from `.env` using Pydantic `BaseSettings`.
The app refuses to start if no AI provider key is present.

---

### API Layer (`app/api/routers/`)

| Router | Endpoint | Purpose |
|---|---|---|
| `chat.py` | `POST /chat` | Multi-turn AI librarian conversation |
| `search.py` | `POST /search/books` | Semantic vector search with pagination |
| `search.py` | `POST /search/ask` | RAG Q&A grounded in the catalogue |
| `classify.py` | `POST /classify` | Support ticket → structured JSON |
| `summarise.py` | `POST /summarise` | Book entry → AI summary |
| `health.py` | `GET /health` | Provider + service health check |

The API layer holds **no business logic** — it validates inputs via Pydantic and delegates to services.

---

### Service Layer (`app/services/`)

#### `ChatService`
Orchestrates multi-turn conversation:
1. Auto-generate or reuse `conversation_id`
2. Enforce session message cap (pre-AI check)
3. Load + truncate conversation history
4. **Classify intent** → route to RAG or skip
5. Build system + user prompt based on intent and catalogue results
6. Call `ResilientAIService.generate()`
7. Track usage, save turn to `ConversationStore`

#### Intent Routing (final design)

```
Message
  └─► _classify_intent()   [temp=0, max_tokens=10 — cheap & fast]
            │
    ┌───────┼────────────┐
    ▼       ▼            ▼
catalogue  book_      general
_lookup    knowledge  (off-topic)
    │       │            │
    ▼       ▼            └──► skip RAG
  RAG      RAG               polite redirect
    │       │
    └───────┤
      Catalogue has results?
            │
           YES ──► upgrade intent to catalogue_lookup
                   AI grounded in results
                   sources populated ✅
            │
           NO  ──► book_knowledge: AI uses general knowledge
                   general: warm redirect to books
```

#### `RAGService`
Full RAG pipeline for `POST /search/ask`:
1. Cache check (namespace `rag:v1`)
2. Rate limit acquire
3. Embed question → vector
4. ChromaDB similarity search (top-K)
5. Apply genre / year filters
6. Drop results below `RAG_RELEVANCE_THRESHOLD`
7. If no results → warm helpful message with search tips
8. Build grounded prompt → AI generate
9. Track usage, cache result

#### `EmbeddingService`
Converts raw text to dense vectors via the active AI provider.
Used by both the seed script (book ingestion) and runtime search.

#### `ClassificationService`
Classifies patron support tickets into:
- **Category**: account / borrowing / technical / complaint / suggestion / general
- **Priority**: low / medium / high / urgent
- **Sentiment**: positive / neutral / negative
- **Department**: Circulation / IT Support / Collections / Reference / Membership / Billing / Administration
- **Summary**: ≤12-word description

#### `SummarisationService`
Generates concise AI summaries of book catalogue entries.

---

### Infrastructure Layer (`app/infrastructure/`)

| Component | Purpose |
|---|---|
| `ConversationStore` | In-memory dict of `conversation_id → [messages]`. Redis in production. |
| `CacheService` | Deterministic key → cached response. Avoids repeated AI calls for identical queries. |
| `TokenBucketRateLimiter` | Prevents API abuse. Blocks when token bucket is empty. |
| `UsageTracker` | Counts prompt + completion tokens, estimates USD cost per provider and model. |
| `ChromaVectorStore` | Thin wrapper around ChromaDB for `search()` and `add()` operations. |

---

### AI Provider Layer (`app/providers/`)

```
ResilientAIService
  ├── 🟢 OpenAI    (primary — fastest, default)
  ├── 🟡 Claude    (fallback 1 — if OpenAI fails or quota exceeded)
  └── 🔵 Gemini   (fallback 2 — last resort)

All fail → RuntimeError → API returns 503 Service Unavailable
```

All providers implement the same `BaseAIProvider` interface so they are interchangeable.

---

### Storage Layer

| Component | Purpose |
|---|---|
| `data/books.json` | Source of truth for the library catalogue |
| `scripts/seed_books.py` | Embeds each book and upserts into ChromaDB |
| `chroma_db/` | Local persistent vector store (auto-created on first seed) |

---

## Data Flow Summary

### Chat (`POST /chat`)

```
Client → POST /chat
  └─► ChatService
        ├─ classify_intent()    [AI call — temp=0, ≤10 tokens]
        ├─ if catalogue/book: retrieve_context()
        │     └─ EmbeddingService → ChromaDB → filter → book list
        ├─ build_system_prompt(intent, has_context)
        ├─ build_user_prompt(history, context, message, intent)
        ├─ ResilientAIService.generate()
        ├─ usage_tracker.record_usage()
        └─ conversation_store.append_message()
  └─► { reply, sources, conversation_id }
```

### Search/Ask (`POST /search/ask`)

```
Client → POST /search/ask
  └─► RAGService
        ├─ cache_service.get(key)          → HIT: return cached
        ├─ rate_limiter.acquire()
        ├─ embedding_service.embed_text()
        ├─ vector_store.search(top_k)
        ├─ apply_filters(genre, year)
        ├─ filter_results(score >= threshold)
        ├─ if empty: return warm "no results" message with search tips
        ├─ build_system_prompt() + build_user_prompt(context)
        ├─ ResilientAIService.generate()
        ├─ usage_tracker.record_usage()
        └─ cache_service.set(key, result)
  └─► { answer, sources, cached }
```

---

*LibraryMind · Final Architecture Documentation*
