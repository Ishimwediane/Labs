# LibraryMind — Part 5: AI Librarian Chatbot Architecture

> **Scope:** `/chat` endpoint — multi-turn, memory-aware, RAG-grounded conversation.

---

## System Architecture Diagram

![LibraryMind Part 5 — AI Librarian Chatbot Architecture](./part5_chatbot_architecture.png)

---

## Architecture Overview

Part 5 builds the **AI Librarian Chatbot** on top of everything built in Parts 0–4.
The key upgrade over Part 4 (one-shot RAG) is **persistent conversation memory**: the
chatbot remembers previous turns within a session, so follow-up questions like
*"Tell me more about that one"* resolve correctly.

---

## Layer-by-Layer Breakdown

### Layer 1 — User / Client

The patron sends a `POST /chat` request containing:

```json
{
  "conversation_id": "a3f9c1-...",
  "message": "Is there a sequel to the one you mentioned?"
}
```

If `conversation_id` is omitted, the server creates a new UUID and starts a fresh session.

---

### Layer 2 — API Layer (`POST /chat`)

| Component | Role |
|---|---|
| FastAPI route | Receives the HTTP request |
| Pydantic `ChatRequest` | Validates input fields |
| Pydantic `ChatResponse` | Formats the final JSON reply |

The API layer holds **no business logic** — it delegates entirely to `ChatService`.

---

### Layer 3 — ChatService (Orchestration)

The core of Part 5. Full execution order:

1. **Conversation ID Handler** — reuse existing ID or generate new UUID
2. **History Loader** — fetch previous messages from `ConversationStore`
3. **History Truncation** — keep only the last N messages (e.g. 10) to stay within the LLM context window
4. **RAG Context Retrieval** — embed the current message → search ChromaDB → filter by relevance score

**Decision Branch:**

| Condition | Action |
|---|---|
| Relevant books found | **Prompt Builder A** — System + History + Book Context + Question |
| No relevant books | **Prompt Builder B** — System + History + "no results" note + Question |

5. **AI Reply Generator** — calls `ResilientAIService.generate()`
6. **History Saver** — appends both user message and assistant reply to the conversation store

---

### Layer 4 — Conversation Memory Store

```python
# Conceptual structure
{
  "conv_id: abc123": [
      {"role": "user",      "content": "..."},
      {"role": "assistant", "content": "..."},
  ],
  "conv_id: xyz789": [
      {"role": "user",      "content": "..."},
      {"role": "assistant", "content": "..."},
  ]
}
```

- **Isolation**: each `conversation_id` key is completely separate.
- **MVP**: plain Python `dict` (in-memory).
- **Production**: Redis for persistence across restarts.

**Truncation rule:** Before building the prompt, only `history[-N:]` is used.
Older messages are kept in the store for records but not sent to the LLM.

---

### Layer 5 — RAG / Knowledge Layer (reused from Part 4)

| Component | Role |
|---|---|
| `EmbeddingService` | Converts the current user message to a vector |
| `ChromaVectorStore` | Finds top-K most semantically similar books |
| Relevance Filter | Drops results below `RAG_RELEVANCE_THRESHOLD` |
| Book Metadata | Title, author, description passed into the prompt |
| `books.json` | Original data source, already seeded into ChromaDB |

> No changes to Part 4 files. ChatService calls the same retrieval logic.

---

### Layer 6 — AI Provider Layer (reused from Part 3)

```
ResilientAIService
    ├── 🟢 OpenAI    ← primary
    ├── 🟡 Claude    ← fallback 1 (if OpenAI fails)
    └── 🔵 Gemini   ← fallback 2 (if Claude also fails)
```

If all providers fail → `RuntimeError` → API returns `503 Service Unavailable`.

---

### Layer 7 — Output

```json
{
  "conversation_id": "a3f9c1-...",
  "reply": "Yes — Dune Messiah by Frank Herbert is the direct sequel...",
  "sources": [
    {"title": "Dune Messiah", "author": "Frank Herbert", "score": 0.88}
  ],
  "turn": 3
}
```

The client stores `conversation_id` and sends it with every subsequent message.

---

## Key Concepts at a Glance

| Concept | What it means |
|---|---|
| **Conversation ID** | A unique UUID that groups all messages in one chat session |
| **Message History** | A list of `{"role": "user/assistant", "content": "..."}` dicts per session |
| **Truncation** | Only the last N messages are sent to the LLM to control cost and context size |
| **RAG in Chat** | The current message is embedded and searched every turn to ground the reply in the catalogue |
| **Follow-up resolution** | The history block in the prompt lets the LLM understand references like "that one" |
| **Grounding** | The system prompt forbids the model from inventing books not in the retrieved context |

---

## New Files Added in Part 5

| File | Purpose |
|---|---|
| `app/api/chat.py` | FastAPI `/chat` route |
| `app/services/chat_service.py` | Multi-turn orchestration logic |
| `app/infrastructure/conversation_store.py` | Per-session message history storage |
| `docs/chatbot_architecture.md` | This document |
| `docs/part5_chatbot_architecture.png` | Architecture diagram |

---

## Mermaid Flowchart

```mermaid
flowchart TB
    subgraph CLIENT["Layer 1 · User / Client"]
        PATRON["Patron"]
        UI["Frontend / Swagger UI / Postman"]
        PATRON -->|"sends message + conversation_id"| UI
    end

    subgraph API["Layer 2 · API Layer"]
        ENDPOINT["POST /chat  FastAPI Route"]
        VALIDATE["Pydantic Validation  ChatRequest"]
        FORMATTER["JSON Response Formatter  ChatResponse"]
        ENDPOINT --> VALIDATE
    end

    subgraph CHAT["Layer 3 · ChatService"]
        direction TB
        CONV_ID["Conversation ID Handler\nnew UUID if none provided"]
        LOAD_HIST["History Loader\nfetch from store"]
        TRUNCATE["History Truncation\nkeep last N messages"]
        RAG_CALL["RAG Context Retrieval\nembed + search ChromaDB"]
        RAG_FOUND{"Relevant catalogue\nresults found?"}
        PROMPT_A["Prompt Builder A\nSystem + History + Context + Question"]
        PROMPT_B["Prompt Builder B\nSystem + History + No-context note"]
        AI_CALL["AI Reply Generator\nResilientAIService.generate()"]
        SAVE_HIST["History Saver\nappend user + assistant turns"]

        CONV_ID --> LOAD_HIST --> TRUNCATE --> RAG_CALL
        RAG_CALL --> RAG_FOUND
        RAG_FOUND -->|"YES — books found"| PROMPT_A
        RAG_FOUND -->|"NO — no matches"| PROMPT_B
        PROMPT_A --> AI_CALL
        PROMPT_B --> AI_CALL
        AI_CALL --> SAVE_HIST
    end

    subgraph MEMORY["Layer 4 · Conversation Memory Store"]
        direction LR
        NEW_OR_EX{"New or existing\nconversation?"}
        STORE_A["conv_id: abc123\n[user msg][assistant reply]..."]
        STORE_B["conv_id: xyz789\n[user msg][assistant reply]..."]
        NEW_OR_EX -->|"New ID"| STORE_A
        NEW_OR_EX -->|"Existing ID"| STORE_B
    end

    subgraph RAG["Layer 5 · RAG / Knowledge Layer"]
        direction LR
        EMB["EmbeddingService\ntext → vector"]
        CHROMA["ChromaDB\nsemantic search"]
        FILTER["Relevance Filter\nscore >= threshold"]
        META["Book Metadata\ntitle · author · description"]
        BOOKS_JSON["books.json"]
        BOOKS_JSON -.->|"seeded into"| CHROMA
        EMB --> CHROMA --> FILTER --> META
    end

    subgraph PROVIDERS["Layer 6 · AI Provider Layer"]
        direction LR
        RESILIENT["ResilientAIService"]
        OPENAI["OpenAI  primary"]
        CLAUDE["Claude  fallback 1"]
        GEMINI["Gemini  fallback 2"]
        PFAIL{"Provider failed?"}
        RESILIENT --> OPENAI --> PFAIL
        PFAIL -->|"YES"| CLAUDE --> PFAIL
        PFAIL -->|"YES"| GEMINI
        PFAIL -->|"NO — success"| RESILIENT
    end

    subgraph OUTPUT["Layer 7 · Output"]
        REPLY["Assistant Reply  grounded answer"]
        SOURCES["Sources  title · author · score"]
        UPDATED["Conversation Updated"]
        REPLY --- SOURCES --- UPDATED
    end

    UI -->|"POST /chat"| ENDPOINT
    VALIDATE -->|"valid"| CONV_ID
    VALIDATE --> NEW_OR_EX

    LOAD_HIST <-->|"read"| STORE_A
    LOAD_HIST <-->|"read"| STORE_B
    SAVE_HIST -->|"write"| STORE_A
    SAVE_HIST -->|"write"| STORE_B

    RAG_CALL --> EMB
    META -->|"book context block"| PROMPT_A

    AI_CALL --> RESILIENT
    RESILIENT -->|"generated text"| AI_CALL

    SAVE_HIST --> FORMATTER
    FORMATTER -->|"JSON response"| UI
    FORMATTER --> REPLY
```

---

*LibraryMind · Part 5 · AI Librarian Chatbot · Architecture Documentation*
