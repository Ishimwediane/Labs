# LibraryMind — Chat Service Architecture

> **Scope:** `POST /chat` — multi-turn, memory-aware, intent-routed, RAG-grounded conversation.

---

## What Changed (Final Version)

The original chat service always called RAG for every message. The final version adds an **Intent Router** that classifies each message first, so the AI gives the right answer for every type of question — without wasting RAG calls or saying "I don't know."

| Old Behaviour | Final Behaviour |
|---|---|
| Always calls RAG | Classifies intent first, then routes |
| Returns "I don't know" for general questions | Answers general book questions from AI knowledge |
| `sources: []` for book knowledge questions | Tries catalogue first — sources populated when found |
| Off-topic questions answered freely | Off-topic questions get a polite redirect to books |
| One fixed system prompt | Three context-aware system prompt modes |

---

## Intent Classification

Before any RAG call, the service runs a lightweight classification:

```python
_classify_intent(message)
  → "catalogue_lookup"   # asks about books in THIS library
  → "book_knowledge"     # asks about books/authors in general
  → "general"            # unrelated to books entirely
```

**Cost:** `temperature=0`, `max_tokens=10` — the cheapest possible AI call.

### Routing Decision Table

| Intent | RAG called? | Catalogue found? | Final behaviour |
|---|---|---|---|
| `catalogue_lookup` | ✅ Yes | ✅ Yes | Grounded in catalogue + sources |
| `catalogue_lookup` | ✅ Yes | ❌ No | Warm "not in our collection" message |
| `book_knowledge` | ✅ Yes | ✅ Yes | Intent upgraded → grounded in catalogue + sources |
| `book_knowledge` | ✅ Yes | ❌ No | AI answers from general literary knowledge |
| `general` | ❌ No | — | Polite redirect back to books |

---

## Full Execution Flow

```mermaid
flowchart TB
    classDef client  fill:#e0f0ff,stroke:#3399ff,stroke-width:2px
    classDef api     fill:#fff0cc,stroke:#ffaa00,stroke-width:2px
    classDef svc     fill:#e8f5e9,stroke:#4caf50,stroke-width:2px
    classDef intent  fill:#fce4ec,stroke:#e91e63,stroke-width:2px
    classDef rag     fill:#f3e5f5,stroke:#9c27b0,stroke-width:2px
    classDef ai      fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    classDef store   fill:#fff8e1,stroke:#ff8f00,stroke-width:2px
    classDef out     fill:#e8f5e9,stroke:#388e3c,stroke-width:2px

    subgraph CLIENT["Layer 1 · Client"]
        PATRON["👤 Patron"]:::client
        UI["Frontend / Postman / Swagger"]:::client
        PATRON -->|"message + conversation_id"| UI
    end

    subgraph APILAYER["Layer 2 · API (POST /chat)"]
        ENDPOINT["FastAPI Route"]:::api
        VALIDATE["Pydantic ChatRequest\nvalidation"]:::api
        FORMATTER["Pydantic ChatResponse\nJSON formatter"]:::api
        ENDPOINT --> VALIDATE
    end

    subgraph CHATSVC["Layer 3 · ChatService (Orchestration)"]
        direction TB
        CONV_ID["1. Conversation ID\nauto-generate UUID if missing"]:::svc
        MSGCAP["2. Session Cap Check\nmax messages enforced pre-AI"]:::svc
        LOAD_HIST["3. History Loader\nfetch from ConversationStore"]:::svc
        TRUNCATE["4. History Truncation\nkeep last N turns"]:::svc
        CLASSIFY_STEP["5. _classify_intent()\ntemp=0, max_tokens=10"]:::intent

        subgraph ROUTING["6. Intent Router"]
            direction LR
            CAT_ROUTE["catalogue_lookup\n→ call RAG"]:::intent
            BOOK_ROUTE["book_knowledge\n→ call RAG\n(try catalogue first)"]:::intent
            GEN_ROUTE["general\n→ skip RAG\npolite redirect"]:::intent
        end

        RAG_RESULT{"7. Catalogue\nresults found?"}:::svc
        UPGRADE["Upgrade intent to\ncatalogue_lookup"]:::intent
        BUILD_SYS["8. Build System Prompt\n(intent-aware mode)"]:::svc
        BUILD_USER["9. Build User Prompt\n(history + context/instruction)"]:::svc
        AI_CALL["10. ResilientAIService\n.generate()"]:::ai
        TRACK["11. Usage Tracker\nrecord tokens + cost"]:::svc
        SAVE["12. ConversationStore\nappend user + assistant turns"]:::svc

        CONV_ID --> MSGCAP --> LOAD_HIST --> TRUNCATE --> CLASSIFY_STEP
        CLASSIFY_STEP --> ROUTING
        CAT_ROUTE & BOOK_ROUTE --> RAG_RESULT
        GEN_ROUTE --> BUILD_SYS
        RAG_RESULT -->|"YES + book_knowledge"| UPGRADE --> BUILD_SYS
        RAG_RESULT -->|"YES + catalogue_lookup"| BUILD_SYS
        RAG_RESULT -->|"NO"| BUILD_SYS
        BUILD_SYS --> BUILD_USER --> AI_CALL --> TRACK --> SAVE
    end

    subgraph MEMLAYER["Layer 4 · Conversation Memory Store"]
        direction LR
        STORE_A["conv_id: abc123\n[user][assistant][user][assistant]..."]:::store
        STORE_B["conv_id: xyz789\n[user][assistant]..."]:::store
    end

    subgraph RAGLAYER["Layer 5 · RAG Pipeline"]
        direction LR
        EMB["EmbeddingService\ntext → vector"]:::rag
        CHROMA["ChromaDB\nsemantic similarity search"]:::rag
        FILT["Relevance Filter\nscore ≥ RAG_RELEVANCE_THRESHOLD"]:::rag
        META["Book Metadata\ntitle · author · description · score"]:::rag
        EMB --> CHROMA --> FILT --> META
    end

    subgraph PROVLAYER["Layer 6 · AI Provider Layer"]
        direction LR
        RESILIENT["ResilientAIService"]:::ai
        OPENAI["🟢 OpenAI\nprimary"]:::ai
        CLAUDE["🟡 Claude\nfallback 1"]:::ai
        GEMINI["🔵 Gemini\nfallback 2"]:::ai
        RESILIENT --> OPENAI
        OPENAI -..->|"fails"| CLAUDE
        CLAUDE -..->|"fails"| GEMINI
    end

    subgraph OUTPUT["Layer 7 · Response"]
        REPLY["reply\ngrounded or general answer"]:::out
        SOURCES["sources\ntitle · author · score\n(empty if no catalogue match)"]:::out
        CONV["conversation_id"]:::out
    end

    %% Wiring
    UI -->|"POST /chat"| ENDPOINT
    VALIDATE -->|"valid request"| CONV_ID
    VALIDATE --> STORE_A

    LOAD_HIST <-->|"read history"| STORE_A & STORE_B
    SAVE -->|"write turn"| STORE_A & STORE_B

    CAT_ROUTE & BOOK_ROUTE -->|"embed + search"| EMB
    META -->|"book context"| BUILD_USER

    AI_CALL --> RESILIENT
    RESILIENT -->|"generated text"| AI_CALL

    SAVE --> FORMATTER
    FORMATTER -->|"JSON"| UI
    FORMATTER --> REPLY & SOURCES & CONV
```

---

## System Prompt Modes

The system prompt changes based on intent and whether the catalogue returned results:

### Mode A — Catalogue results found (`catalogue_lookup` + results)
```
CATALOGUE SEARCH MODE — Books were found:
1. ONLY discuss books in the Library Catalogue Context
2. NEVER invent titles, authors, ISBNs, or plot details
3. Cite exact title and author from catalogue
4. Highlight relevance; compare multiple matches
```

### Mode B — Catalogue miss (`catalogue_lookup` + no results)
```
CATALOGUE SEARCH MODE — No matching books found:
1. Apologise warmly and honestly
2. Suggest different keywords or genres
3. MAY mention 1-2 well-known books from general knowledge
   (clearly NOT in this library)
4. Invite patron to ask about something else
```

### Mode C — General book knowledge (`book_knowledge` + no catalogue match)
```
BOOK KNOWLEDGE MODE:
1. Answer from general literary knowledge
2. Be accurate — no invented facts
3. Invite patron to search the LibraryMind catalogue
4. Keep focused on books and reading
```

### Mode D — Off-topic (`general`)
```
OUT-OF-SCOPE MESSAGE:
1. Politely acknowledge the question
2. Explain you specialise in books and reading
3. Redirect with a warm invitation to search
4. Brief, friendly, never dismissive
Example: "That's a bit outside my bookshelf! Is there a book I can find for you?"
```

---

## User Prompt Structure

```
=== Conversation History ===          (if any)
Patron: ...
Librarian: ...

=== Library Catalogue Results ===     (if catalogue_lookup + results)
BOOK 1:
  Title:  The Name of the Rose
  Author: Umberto Eco
  Relevance score: 0.87

LIMITATION: You may only refer to books listed above.

            OR

=== Library Catalogue Results ===     (if catalogue_lookup + no results)
No books matched this search.
Apologise warmly, suggest alternatives...

            OR

=== Instruction ===                   (if book_knowledge or general)
[context-appropriate instruction]

=== Patron's Message ===
<message>

Librarian (Mira) Response:
```

---

## Conversation Memory

```python
# ConversationStore internal structure
{
  "conv-id-abc": [
    {"role": "user",      "content": "Do you have sci-fi books?"},
    {"role": "assistant", "content": "Yes! We have Dune by Frank Herbert..."},
    {"role": "user",      "content": "Tell me more about that one"},
    {"role": "assistant", "content": "Dune is set on the desert planet Arrakis..."},
  ]
}
```

- **Isolation:** each `conversation_id` is completely independent
- **Truncation:** only `history[-N:]` is sent to the LLM (controlled by `CHAT_HISTORY_LIMIT`)
- **Cap:** sessions are hard-capped at `MAX_MESSAGES_PER_SESSION` turns

---

## Key Files

| File | Role |
|---|---|
| [`app/api/routers/chat.py`](../app/api/routers/chat.py) | FastAPI `/chat` route + error handling |
| [`app/services/chat_service.py`](../app/services/chat_service.py) | All orchestration, intent routing, prompt building |
| [`app/services/rag_service.py`](../app/services/rag_service.py) | RAG pipeline called by the chat service |
| [`app/infrastructure/conversation_store.py`](../app/infrastructure/conversation_store.py) | Per-session message history |

---

## Example Conversations

### Book in catalogue
```
Patron:    "Do you have mystery books set in Paris?"
Intent:    catalogue_lookup
RAG:       ✅ called → 2 books found
Sources:   [{ title, author, score }]
Reply:     "Great news! We have 'The Murders of Rue Morgue'..."
```

### Book knowledge (catalogue miss)
```
Patron:    "Who wrote Harry Potter?"
Intent:    book_knowledge
RAG:       ✅ called → no match
Sources:   []
Reply:     "Harry Potter was written by J.K. Rowling..."
           "Would you like me to search our catalogue for fantasy fiction?"
```

### Off-topic
```
Patron:    "What's the capital of France?"
Intent:    general
RAG:       ❌ skipped
Sources:   []
Reply:     "That's a bit outside my bookshelf! I'm your LibraryMind
            assistant — best at helping you discover great reads.
            Is there a book or topic I can search for you today?"
```

---

*LibraryMind · Chat Service · Final Architecture Documentation*
