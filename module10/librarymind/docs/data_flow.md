# LibraryMind — Data Flow Diagrams

Each diagram shows the full request lifecycle for one endpoint, from HTTP in to HTTP out.

---

## Shared infrastructure on every request

Before any endpoint logic runs, two cross-cutting checks fire:

```mermaid
flowchart LR
    REQ([HTTP Request]) --> RL{Rate limiter\ntokens > 0?}
    RL -->|No| E429([429 Too Many Requests])
    RL -->|Yes| ROUTER[Route handler]
    ROUTER --> RESP([HTTP Response])
```

---

## 1. `POST /search/books` — Semantic book search

```mermaid
flowchart TD
    A([Client sends query + limit]) --> B[EmbeddingService\nembed query text]
    B --> C[ChromaVectorStore\ncosine similarity search\ntop-K candidates]
    C --> D[Filter & rank\nby similarity score]
    D --> E[Build BookResult list\nid · title · author · genre\nyear · description · score]
    E --> F([Return BookSearchResponse\nresults · total · query])
```

**Key components:** `EmbeddingService` → `ChromaVectorStore`  
**No AI call, no cache** — pure vector search.

---

## 2. `POST /search/ask` — RAG question answering

```mermaid
flowchart TD
    A([Client sends question]) --> B[CacheService\ncheck Redis\nkey = sha256 of question]
    B -->|Cache HIT| Z([Return cached AskResponse\ncached=true])
    B -->|Cache MISS| C[EmbeddingService\nembed question]
    C --> D[ChromaVectorStore\nretrieve top-K books]
    D --> E{score >=\nRAG_RELEVANCE_THRESHOLD\n0.7?}
    E -->|No — discard| E
    E -->|Yes — keep| F[Build RAG prompt\ninjecting book context]
    F --> G[ResilientAIService\namalitech → openai → anthropic → gemini]
    G -->|Success| H[UsageTracker\nrecord tokens + cost]
    H --> I[CacheService\nstore response in Redis\nTTL = 3600s]
    I --> J([Return AskResponse\nanswer · sources · cached=false])
    G -->|All providers fail| K([503 Service Unavailable])
```

**Key components:** `CacheService` → `EmbeddingService` → `ChromaVectorStore` → `RAGService` → `ResilientAIService` → `UsageTracker` → `CacheService`

---

## 3. `POST /chat` — Multi-turn librarian chat

```mermaid
flowchart TD
    A([Client sends conversation_id + message]) --> B[ConversationStore\nload history for conversation_id\ncapped at CHAT_HISTORY_LIMIT]
    B --> C[EmbeddingService\nembed current message]
    C --> D[ChromaVectorStore\nretrieve top-K relevant books]
    D --> E{score >=\nRAG_RELEVANCE_THRESHOLD?}
    E -->|Yes| F[Build prompt\nsystem prompt + book context\n+ conversation history\n+ current message]
    E -->|No context found| F
    F --> G[ResilientAIService\namalitech → openai → anthropic → gemini]
    G -->|Success| H[ConversationStore\nappend user message]
    H --> I[ConversationStore\nappend assistant reply]
    I --> J[UsageTracker\nrecord tokens + cost]
    J --> K([Return ChatResponse\nreply · sources · conversation_id])
    G -->|All providers fail| L([503 Service Unavailable])
```

**Key components:** `ConversationStore` → `EmbeddingService` → `ChromaVectorStore` → `ChatService` → `ResilientAIService` → `ConversationStore` → `UsageTracker`

**Memory management:** History is truncated to the most recent `CHAT_HISTORY_LIMIT` (default 10) messages before being injected into the prompt, keeping token usage bounded.

---

## 4. `POST /classify/ticket` — Support ticket classification

```mermaid
flowchart TD
    A([Client sends ticket_text]) --> B[ClassificationService\nbuild structured prompt\nasking for JSON output:\ncategory · priority · sentiment\ndepartment · summary]
    B --> C[ResilientAIService\namalitech → openai → anthropic → gemini]
    C -->|Raw text response| D{Valid JSON\nin response?}
    D -->|Yes| E[Parse JSON\ninto TicketClassificationResponse]
    D -->|No — retry parse\nor raise error| F([503 Service Unavailable])
    E --> G[UsageTracker\nrecord tokens + cost]
    G --> H([Return TicketClassificationResponse\ncategory · priority · sentiment\ndepartment · summary])
    C -->|All providers fail| F
```

**Key components:** `ClassificationService` → `ResilientAIService` → `UsageTracker`  
**No vector search, no cache** — pure LLM classification with JSON output parsing.

---

## 5. `POST /summarise/reviews` — Review summarisation

```mermaid
flowchart TD
    A([Client sends list of 1–50 reviews]) --> B[SummarisationService\ncombine reviews into prompt\nasking for JSON output:\noverall_sentiment · average_rating\nkey_themes · praise · criticism\nrecommendation]
    B --> C[ResilientAIService\namalitech → openai → anthropic → gemini]
    C -->|Raw text response| D{Valid JSON\nin response?}
    D -->|Yes| E[Parse JSON\ninto ReviewSummarisationResponse]
    D -->|No — retry parse\nor raise error| F([503 Service Unavailable])
    E --> G[UsageTracker\nrecord tokens + cost]
    G --> H([Return ReviewSummarisationResponse\noverall_sentiment · average_rating\nkey_themes · praise · criticism\nrecommendation])
    C -->|All providers fail| F
```

**Key components:** `SummarisationService` → `ResilientAIService` → `UsageTracker`  
**No vector search, no cache** — pure LLM analysis with JSON output parsing.

---

## 6. `GET /health`

```mermaid
flowchart LR
    A([Client GET /health]) --> B[UsageTracker\nget_total_requests]
    B --> C[UsageTracker\nget_daily_cost]
    C --> D([Return HealthResponse\nstatus · environment\nprimary_provider\ntotal_requests · daily_cost_usd])
```

---

## Provider fallback flow (shared by all AI calls)

```mermaid
flowchart TD
    S([ResilientAIService.generate]) --> P1[Try PRIMARY_PROVIDER\ne.g. amalitech]
    P1 -->|Success| RET([Return result])
    P1 -->|Exception\nafter 3 retries| P2[Try next provider\ne.g. openai]
    P2 -->|Success| RET
    P2 -->|Exception| P3[Try next provider\ne.g. anthropic]
    P3 -->|Success| RET
    P3 -->|Exception| P4[Try next provider\ne.g. gemini]
    P4 -->|Success| RET
    P4 -->|Exception| ERR([RuntimeError — all providers failed\n→ 503 Service Unavailable])
```

Provider order is: `PRIMARY_PROVIDER` first, then the remaining initialised providers in the order they appear in `_initialize_providers` (openai → anthropic → gemini → amalitech).
