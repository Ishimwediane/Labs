# LibraryMind — API Reference

Base URL: `http://localhost:8000`  
Interactive docs: `http://localhost:8000/docs`

---

## Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/` | Project metadata |
| GET | `/health` | Server status + usage metrics |
| POST | `/search/books` | Semantic book search |
| POST | `/search/ask` | RAG question answering |
| POST | `/chat` | Multi-turn librarian chat |
| POST | `/classify/ticket` | Support ticket classification |
| POST | `/summarise/reviews` | Review batch summarisation |

---

## `GET /`

Returns project metadata and navigation links. No request body.

**Response `200`**
```json
{
  "name": "LibraryMind",
  "version": "1.0.0",
  "environment": "development",
  "docs": "/docs",
  "health": "/health"
}
```

---

## `GET /health`

Returns server status and aggregated AI usage metrics.

**Response `200`**
```json
{
  "status": "ok",
  "environment": "development",
  "primary_provider": "amalitech",
  "total_requests": 42,
  "daily_cost_usd": 0.0031
}
```

---

## `POST /search/books`

Semantic vector search over the library catalogue. Returns the top matching books ranked by similarity score.

**Request body**
```json
{
  "query": "fantasy novels with dragons and magic",
  "limit": 5
}
```

| Field | Type | Rules | Default |
|---|---|---|---|
| `query` | string | 3–500 chars, required | — |
| `limit` | integer | 1–20 | `5` |

**Response `200`**
```json
{
  "results": [
    {
      "id": "book_003",
      "title": "The Dragon's Oath",
      "author": "Mira Fontaine",
      "genre": "Fantasy",
      "year": 2021,
      "description": "A young mage forges a forbidden bond with an ancient dragon...",
      "score": 0.91
    }
  ],
  "total": 1,
  "query": "fantasy novels with dragons and magic"
}
```

**Status codes**

| Code | Meaning |
|---|---|
| `200` | Results returned (may be empty list) |
| `422` | Validation error — query too short/long or limit out of range |
| `429` | Rate limit exceeded |

---

## `POST /search/ask`

RAG-powered Q&A. The answer is grounded exclusively in the library catalogue — the AI will not answer from general knowledge.

**Request body**
```json
{
  "question": "What science fiction books do you have about space exploration?"
}
```

| Field | Type | Rules |
|---|---|---|
| `question` | string | 5–500 chars, required |

**Response `200`**
```json
{
  "answer": "We have several science fiction titles about space exploration in our catalogue. 'The Starlight Voyager' by Elena Vance (2024) follows an astronaut on a 200-year mission...",
  "sources": [
    {
      "id": "book_001",
      "title": "The Starlight Voyager",
      "author": "Elena Vance",
      "score": 0.88
    }
  ],
  "cached": false
}
```

| Field | Type | Description |
|---|---|---|
| `answer` | string | AI-generated answer grounded in catalogue |
| `sources` | array | Books used as context (scored above relevance threshold) |
| `cached` | boolean | `true` if response came from Redis cache |

**Status codes**

| Code | Meaning |
|---|---|
| `200` | Answer returned |
| `422` | Validation error |
| `429` | Rate limit exceeded |
| `503` | All AI providers failed |

---

## `POST /chat`

Multi-turn conversation with an AI librarian. Maintains per-conversation memory. Use the **same `conversation_id`** across turns to continue a session.

**Request body**
```json
{
  "conversation_id": "user-session-abc123",
  "message": "Can you recommend a good mystery novel?"
}
```

| Field | Type | Rules |
|---|---|---|
| `conversation_id` | string | 1–128 chars, required. Use a UUID or any stable identifier. |
| `message` | string | 1–2000 chars, required |

**Response `200`**
```json
{
  "reply": "Based on our catalogue, I'd recommend 'The Hollow Clock' by James Osei — a classic locked-room mystery set in 1920s London with excellent reviews.",
  "sources": [
    {
      "id": "book_017",
      "title": "The Hollow Clock",
      "author": "James Osei",
      "score": 0.84
    }
  ],
  "conversation_id": "user-session-abc123"
}
```

**Multi-turn example**

Turn 1 — start a new conversation:
```json
{ "conversation_id": "session-001", "message": "I like historical fiction." }
```
Turn 2 — follow-up in the same session:
```json
{ "conversation_id": "session-001", "message": "Which of those are set in ancient Rome?" }
```

**Status codes**

| Code | Meaning |
|---|---|
| `200` | Reply returned |
| `422` | Validation error |
| `429` | Rate limit exceeded |
| `503` | All AI providers failed |

---

## `POST /classify/ticket`

Classifies a support ticket into structured fields: category, priority, sentiment, responsible department, and a short summary.

**Request body**
```json
{
  "ticket_text": "I cannot log into my account. I have tried resetting my password three times and it keeps failing. This is very frustrating — I need access urgently for a school project due tomorrow."
}
```

| Field | Type | Rules |
|---|---|---|
| `ticket_text` | string | 10–2000 chars, required |

**Response `200`**
```json
{
  "category": "account",
  "priority": "urgent",
  "sentiment": "negative",
  "department": "IT Support",
  "summary": "User is unable to log in after multiple failed password resets and requires urgent access for an imminent deadline."
}
```

**Field value enums**

| Field | Allowed values |
|---|---|
| `category` | `account` `borrowing` `technical` `complaint` `suggestion` `general` |
| `priority` | `low` `medium` `high` `urgent` |
| `sentiment` | `positive` `neutral` `negative` |

**Status codes**

| Code | Meaning |
|---|---|
| `200` | Classification returned |
| `422` | Validation error |
| `429` | Rate limit exceeded |
| `503` | All AI providers failed |

---

## `POST /summarise/reviews`

Analyses a batch of 1–50 reviews and returns a structured summary: sentiment, average rating, themes, praise, criticism, and a recommendation sentence.

**Request body**
```json
{
  "reviews": [
    "Absolutely love this library app! The search is incredibly accurate.",
    "The catalogue is huge but the app crashes sometimes on older phones.",
    "Staff recommendations are always spot on. Found so many hidden gems.",
    "Wish there were more audiobooks available. Text selection is great though."
  ]
}
```

| Field | Type | Rules |
|---|---|---|
| `reviews` | array of strings | 1–50 items, required |

**Response `200`**
```json
{
  "overall_sentiment": "positive",
  "average_rating": 3.8,
  "key_themes": [
    "search accuracy",
    "catalogue size",
    "app stability",
    "audiobook availability"
  ],
  "praise": [
    "Highly accurate semantic search",
    "Large and diverse catalogue",
    "Trusted staff recommendations"
  ],
  "criticism": [
    "App crashes on older devices",
    "Limited audiobook selection"
  ],
  "recommendation": "A strong library platform with excellent search and curation; prioritise mobile stability and audiobook expansion to address the main pain points."
}
```

**Field value enums**

| Field | Allowed values |
|---|---|
| `overall_sentiment` | `positive` `negative` `mixed` |
| `average_rating` | float `0.0`–`5.0` |

**Status codes**

| Code | Meaning |
|---|---|
| `200` | Summary returned |
| `422` | Validation error — wrong number of reviews |
| `429` | Rate limit exceeded |
| `503` | All AI providers failed |

---

## Common error shapes

**`422` Validation error**
```json
{
  "detail": [
    {
      "loc": ["body", "query"],
      "msg": "String should have at least 3 characters",
      "type": "string_too_short"
    }
  ]
}
```

**`429` Rate limit exceeded**
```json
{
  "detail": "Rate limit exceeded. Please wait before retrying."
}
```

**`503` Service unavailable**
```json
{
  "detail": "All available AI providers (amalitech, openai, anthropic, gemini) failed to generate a response."
}
```
