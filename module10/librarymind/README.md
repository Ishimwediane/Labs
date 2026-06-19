# LibraryMind — AI-Powered Library Backend

> An intelligent library assistant that combines semantic search, multi-turn conversation memory, and Retrieval-Augmented Generation (RAG) to help patrons discover and explore books.

---

## What LibraryMind Does

| Feature | Endpoint | Description |
|---|---|---|
| Semantic book search | `POST /search/books` | Find books by meaning, not just keywords |
| RAG-powered Q&A | `POST /search/ask` | Ask questions grounded in the library catalogue |
| Multi-turn AI chat | `POST /chat` | Conversational librarian with memory & intent routing |
| Ticket classification | `POST /classify` | Auto-categorise support tickets with AI |
| Book summarisation | `POST /summarise` | Generate AI summaries of catalogue entries |
| Health check | `GET /health` | Service and provider status |

---

## Architecture Overview

```
Patron
  │
  ▼
FastAPI API Layer
  ├── POST /search/books  → EmbeddingService → ChromaDB  → ranked results
  ├── POST /search/ask    → RAGService       → ChromaDB + AI → grounded answer
  ├── POST /chat          → ChatService      → Intent Router → RAG? → AI reply
  ├── POST /classify      → ClassificationService → AI → structured ticket JSON
  └── POST /summarise     → SummarisationService  → AI → book summary
```

---

## Chat Intent Routing (Key Design)

The chat endpoint classifies every message before deciding what to do:

```
Message → _classify_intent()
               │
    ┌──────────┼──────────────┐
    ▼          ▼              ▼
catalogue  book_knowledge  general
_lookup                    (off-topic)
    │          │              │
    ▼          ▼              │
  RAG ──► Catalogue?     Skip RAG
    │      │     │            │
    │    YES     NO           │
    │      │     │            │
    │   upgrade  │            │
    │   intent   │            │
    ▼      │     ▼            ▼
 Grounded  │  AI general   Polite
 answer    │  knowledge    redirect
   +       │  answer       to books
 sources   │  + invite
           │  to search
           ▼
        sources []
```

---

## Setup Instructions

### 1. Prerequisites
- Python 3.10 or higher

### 2. Create & Activate Virtual Environment

**Windows:**
```bash
python -m venv venv
.\venv\Scripts\activate
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Requirements
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
```bash
cp .env.example .env
```

Edit `.env` and provide **at least one** AI provider API key:

| Key | Provider |
|---|---|
| `OPENAI_API_KEY` | OpenAI (GPT-4o, GPT-4, etc.) |
| `ANTHROPIC_API_KEY` | Anthropic (Claude) |
| `GEMINI_API_KEY` | Google Gemini |

> **Required:** The app will not start if no provider key is set.

Key settings to review:

```env
PRIMARY_PROVIDER=openai          # Which provider to use first
RAG_RELEVANCE_THRESHOLD=0.3      # Minimum similarity score for RAG results
RAG_TOP_K=5                      # How many books to retrieve per search
CHAT_HISTORY_LIMIT=10            # Max conversation turns kept in context
MAX_MESSAGES_PER_SESSION=20      # Hard cap before session must be reset
```

### 5. Seed the Book Catalogue
```bash
python scripts/seed_books.py
```

### 6. Start the Server
```bash
uvicorn app.main:app --reload
```

API available at: **http://127.0.0.1:8000**  
Interactive docs: **http://127.0.0.1:8000/docs**

---

## Setup with Docker (Redis & ChromaDB)

Instead of running an embedded persistent vector store and in-memory cache, you can run production-grade Docker containers for both **Redis** and **ChromaDB**.

### 1. Start Docker Containers
Ensure Docker Desktop is running on your machine, then spin up the services from the project root:
```bash
docker-compose up -d
```
This starts:
- **Redis** on port `6379`
- **ChromaDB** on port `8002` (mapped to host port 8002 to avoid port conflicts with FastAPI)

### 2. Configure Environment for Docker
Update your local `.env` file to point to the Dockerized HTTP services:
```env
# Vector Database (Dockerized HTTP mode)
CHROMA_HOST=localhost
CHROMA_PORT=8002

# Redis Cache
REDIS_URL=redis://localhost:6379/0
CACHE_ENABLED=true
```

### 3. Seed the Dockerized ChromaDB Catalog
Since the containerized ChromaDB starts as an empty database volume, re-run the seed script to populate it with the library catalogue:
```bash
python scripts/seed_books.py
```

---


## Project Structure

```text
librarymind/
├── app/
│   ├── api/
│   │   ├── routers/
│   │   │   ├── chat.py           # POST /chat — multi-turn chatbot
│   │   │   ├── search.py         # POST /search/books, POST /search/ask
│   │   │   ├── classify.py       # POST /classify — ticket classification
│   │   │   ├── summarise.py      # POST /summarise — book summarisation
│   │   │   └── health.py         # GET /health
│   │   ├── models.py             # Pydantic request/response models
│   │   └── dependencies.py       # FastAPI dependency injection
│   ├── services/
│   │   ├── chat_service.py       # Multi-turn chat + intent routing
│   │   ├── rag_service.py        # RAG pipeline (search/ask)
│   │   ├── embedding_service.py  # Text → vector conversion
│   │   ├── classification_service.py  # Ticket classification
│   │   └── summarisation_service.py   # Book summarisation
│   ├── infrastructure/
│   │   ├── vector_store.py       # ChromaDB wrapper
│   │   ├── conversation_store.py # Per-session message history
│   │   ├── cache.py              # Redis / in-memory cache
│   │   ├── rate_limiter.py       # Token bucket rate limiter
│   │   └── usage_tracker.py      # Token & cost tracking
│   ├── providers/
│   │   ├── base.py               # Abstract AI provider interface
│   │   ├── openai_provider.py
│   │   ├── anthropic_provider.py
│   │   ├── gemini_provider.py
│   │   └── resilient_service.py  # Auto-fallback across providers
│   ├── utils/
│   │   └── json_output.py        # JSON extraction helpers
│   ├── config.py                 # Pydantic settings + validation
│   └── main.py                   # FastAPI app entry point
├── data/
│   └── books.json                # Catalogue source data
├── scripts/
│   └── seed_books.py             # Seeds books.json → ChromaDB
├── docs/
│   ├── architecture.md           # System architecture diagram
│   ├── chatbot_architecture.md   # Chat service flow diagram
│   ├── rag_architecture.md       # RAG pipeline diagram
│   ├── api_reference.md          # Full API reference
│   └── ...
├── chroma_db/                    # Local ChromaDB vector store (auto-created)
├── .env                          # Your local config (not committed)
├── requirements.txt
└── README.md
```

---

## API Endpoint Testing Guide

Below are copy-pasteable `curl` commands to test every single endpoint of the LibraryMind API. 
*Note: Make sure your server is running locally (e.g. at `http://127.0.0.1:8000`) before running these.*

### 1. Health Check (`GET /health`)
Checks service status, active AI provider, total request count, and estimated daily cost.
```bash
curl -X GET http://127.0.0.1:8000/health
```

### 2. Semantic Book Search (`POST /search/books`)
Finds books matching the concept "dystopian novels about control". Supports pagination query parameters `page` and `limit`.
```bash
curl -X POST "http://127.0.0.1:8000/search/books?page=1&limit=5" \
     -H "Content-Type: application/json" \
     -d "{\"query\": \"dystopian novels about control\", \"genre\": \"Dystopian\", \"year_min\": 1940, \"year_max\": 2000}"
```

### 3. RAG-Powered Q&A (`POST /search/ask`)
Asks a question that is answered strictly based on the books in the library catalogue.
```bash
curl -X POST http://127.0.0.1:8000/search/ask \
     -H "Content-Type: application/json" \
     -d "{\"question\": \"What is the core conflict in the book 1984?\", \"genre\": \"Dystopian\"}"
```

### 4. Multi-Turn AI Librarian Chat (`POST /chat`)
Converses with the librarian agent ("Mira"). Intent routing automatically handles catalogue vs general vs off-topic queries.

#### A. Start a new session (omit `conversation_id`)
```bash
curl -X POST http://127.0.0.1:8000/chat \
     -H "Content-Type: application/json" \
     -d "{\"message\": \"Do you have any mystery books set in Paris?\"}"
```
*Take note of the `"conversation_id"` returned in the JSON response.*

#### B. Continue conversation (pass the conversation ID from step A)
```bash
curl -X POST http://127.0.0.1:8000/chat \
     -H "Content-Type: application/json" \
     -d "{\"conversation_id\": \"YOUR_CONVERSATION_ID_HERE\", \"message\": \"Who is the author of that book?\"}"
```

#### C. List all active chat sessions (`GET /chat/sessions`)
Lists active sessions with status, counts, and previews.
```bash
curl -X GET "http://127.0.0.1:8000/chat/sessions?page=1&limit=10"
```

#### D. Retrieve full session history (`GET /chat/sessions/{conversation_id}`)
Retrieves the complete history of messages for one conversation.
```bash
curl -X GET http://127.0.0.1:8000/chat/sessions/YOUR_CONVERSATION_ID_HERE
```

#### E. Reset session history (`POST /chat/sessions/{conversation_id}/reset`)
Clears history for the session while keeping the session ID valid.
```bash
curl -X POST http://127.0.0.1:8000/chat/sessions/YOUR_CONVERSATION_ID_HERE/reset
```

### 5. Support Ticket Classification (`POST /classify/ticket`)
Automatically classifies support tickets into predefined departments, priority, sentiment, and category.
```bash
curl -X POST http://127.0.0.1:8000/classify/ticket \
     -H "Content-Type: application/json" \
     -d "{\"ticket_text\": \"My library card is locked and I cannot check out my books online. Please help!\"}"
```

### 6. Review Summarisation (`POST /summarise/reviews`)
Analyzes a batch of book reviews to generate a structured summary, average rating, themes, praise, criticism, and recommendation.
```bash
curl -X POST http://127.0.0.1:8000/summarise/reviews \
     -H "Content-Type: application/json" \
     -d "{\"reviews\": [\"Absolutely beautiful writing! The character development was stellar.\", \"The story was interesting but the middle section dragged heavily.\", \"Highly disappointed. The ending was rushed and did not make sense.\"]}"
```

---

## AI Provider Resilience

LibraryMind automatically falls back across providers if one fails:

```
ResilientAIService
  ├── 🟢 OpenAI    ← primary
  ├── 🟡 Claude    ← fallback 1
  └── 🔵 Gemini   ← fallback 2

All fail → 503 Service Unavailable
```

---

## Documentation

| File | Contents |
|---|---|
| [`docs/architecture.md`](docs/architecture.md) | Full system architecture with Mermaid diagram |
| [`docs/chatbot_architecture.md`](docs/chatbot_architecture.md) | Chat service + intent routing flow |
| [`docs/rag_architecture.md`](docs/rag_architecture.md) | RAG pipeline deep-dive |
| [`docs/api_reference.md`](docs/api_reference.md) | All endpoints, request/response models |
| [`http://127.0.0.1:8000/docs`](http://127.0.0.1:8000/docs) | Live Swagger UI (when running) |

---

*LibraryMind — Module 10 · AI-Powered Library Assistant*
