# Deep Dive: `POST /search/books`

This document traces a single HTTP request through every file it touches,
explaining the code and the **"why"** behind every design decision.

---

## The Big Picture

When a client calls `POST /search/books`, the request flows through **4 layers**:

```
HTTP Request
  │
  ▼
1. ROUTER  (search.py)          ← "What URL does this map to?"
  │
  ▼
2. DEPENDENCY INJECTION         ← "What services does this function need?"
   (dependencies.py)
  │
  ▼
3. SERVICES                     ← "Do the actual work"
   ├── EmbeddingService         ← Convert text → numbers (vector)
   └── ChromaVectorStore        ← Search by those numbers
  │
  ▼
4. INFRASTRUCTURE               ← "Talk to external systems"
   ├── CacheService (Redis)     ← Avoid repeating expensive API calls
   └── ChromaDB                 ← The vector database
  │
  ▼
HTTP Response
```

Now let's go file by file.

---

## File 1: `app/main.py` — The Entry Point

Before the request even reaches your code, FastAPI itself must be created.
This is the file you run with `uvicorn app.main:app --reload`.

```python
from fastapi import FastAPI
from app.api.routers import search

app = FastAPI()
app.include_router(search.router)
```

**FastAPI concept — `app`:**
`FastAPI()` creates a web application. Think of it like opening a restaurant:
the `app` object is the restaurant itself. It doesn't serve food yet —
it just exists.

**FastAPI concept — `include_router`:**
`app.include_router(search.router)` is like saying "this restaurant also
has a search menu." Routers let you organise your endpoints into separate
files instead of one giant file. The `search.router` is defined in
`app/api/routers/search.py`.

---

## File 2: `app/api/routers/search.py` — The Router (Entry Point for the Request)

This is the first file your request hits.

```python
router = APIRouter(prefix="/search", tags=["Search"])
```

`APIRouter` is a "mini FastAPI app." The `prefix="/search"` means every
endpoint defined on this router automatically starts with `/search`.
So `/books` becomes `/search/books`.

```python
@router.post(
    "/books",
    response_model=BookSearchResponse,
    ...
)
async def search_books(
    body: BookSearchRequest,
    embedding_svc: Annotated[EmbeddingService, Depends(get_embedding_service)],
    vector_store:  Annotated[ChromaVectorStore,  Depends(get_vector_store)],
) -> BookSearchResponse:
```

There are **3 important concepts** packed into this function signature:

### Concept 1 — `@router.post("/books")`
This decorator registers the function as the handler for
`POST /search/books`. A "decorator" in Python (`@something`) is a wrapper
that adds behaviour to a function. Here it tells FastAPI: "When someone
sends a POST request to /search/books, call `search_books()`."

### Concept 2 — `body: BookSearchRequest` (Automatic Validation)
FastAPI reads the `BookSearchRequest` type hint and automatically:
1. Parses the raw JSON from the HTTP body
2. Validates every field using the rules defined in `BookSearchRequest`
3. If validation fails, it returns a `422 Unprocessable Entity` error
   **before your function is even called**

You never write `json.loads(request.body)` yourself. FastAPI does it.

### Concept 3 — `Depends(get_embedding_service)` (Dependency Injection)
This is FastAPI's killer feature. Instead of creating services inside
your endpoint (which makes testing hard), you **declare** what you need
and FastAPI provides it.

`Depends(get_embedding_service)` means:
> "Before calling `search_books`, call `get_embedding_service()` and give
> me whatever it returns."

The function body is clean — it just uses the services, it never
creates them.

---

## File 3: `app/api/models.py` — The Data Contracts

These are your request/response shapes. Pydantic is the library that powers them.

```python
class BookSearchRequest(BaseModel):
    query: str = Field(
        ...,          # ← The "..." means this field is REQUIRED
        min_length=3,
        max_length=500,
        description="The search query",
    )
    limit: int = Field(
        default=5,    # ← Optional, defaults to 5 if not provided
        ge=1,         # ← ge = "greater than or equal to"
        le=20,        # ← le = "less than or equal to"
    )
```

**Why Pydantic?**
Pydantic models do 3 things at once:
1. **Parse** — convert raw JSON into a Python object
2. **Validate** — enforce rules (`min_length`, `ge`, `le`) automatically
3. **Document** — FastAPI uses these models to auto-generate the Swagger UI docs at `/docs`

If a client sends `{ "query": "hi" }` (too short, min 3 chars), Pydantic
catches it and FastAPI returns:
```json
{ "detail": [{ "msg": "String should have at least 3 characters" }] }
```

```python
class BookResult(BaseModel):
    id: str
    title: str
    author: str
    genre: str
    year: int
    description: str
    score: float  # ← Cosine similarity 0.0 to 1.0

class BookSearchResponse(BaseModel):
    results: list[BookResult]
    total: int
    query: str        # ← Echo the original query back to the client
```

`BookSearchResponse` is the **output contract**. The `response_model=BookSearchResponse`
in the router tells FastAPI to validate and serialize the return value
using this model. Even if your code accidentally includes extra fields,
FastAPI will strip them out.

---

## File 4: `app/api/dependencies.py` — The Factory (Dependency Injection)

This file contains "factory functions" — functions whose only job is to
create and return service objects.

```python
@lru_cache()
def get_embedding_service() -> EmbeddingService:
    logger.info("Initialising EmbeddingService...")
    return EmbeddingService()
```

**Why `@lru_cache()`?**
`@lru_cache()` from Python's standard library makes a function remember
its return value. The first time `get_embedding_service()` is called,
it creates an `EmbeddingService` object. Every call after that **returns
the same object** instead of creating a new one.

This is the **Singleton pattern** — one shared instance for the entire
lifetime of the application. This is critical because:
- `EmbeddingService` connects to OpenAI/Gemini — you don't want to
  re-initialize clients on every request
- The `CacheService` inside `EmbeddingService` holds a Redis connection —
  you want to reuse that connection

```python
@lru_cache()
def get_vector_store() -> ChromaVectorStore:
    logger.info("Initialising ChromaVectorStore...")
    return ChromaVectorStore()
```

Same pattern. One ChromaDB client shared across all requests.

---

## File 5: `app/services/embedding_service.py` — Convert Text → Vector

This service answers the question: **"What does this text MEAN as numbers?"**

### Why do we need embeddings at all?

Computers can't compare the *meaning* of two sentences with `==`.
But if you convert each sentence into a list of numbers (a vector),
you can calculate how close they are mathematically.

```
"space exploration"   → [0.002, -0.018, 0.094, ...]  (1536 numbers)
"astronaut adventure" → [0.004, -0.021, 0.089, ...]  (very close!)
"medieval romance"    → [0.091, 0.043, -0.012, ...]  (far away)
```

This is what an AI embedding model produces.

### The Code

```python
def __init__(self):
    self.settings = get_settings()
    self.cache = CacheService()

    # Primary: OpenAI
    self.openai_client = OpenAI(api_key=self.settings.OPENAI_API_KEY)
    self.openai_model = self.settings.OPENAI_EMBEDDING_MODEL  # "text-embedding-3-small"

    # Fallback: Gemini
    self.gemini_client = genai.Client(api_key=self.settings.GEMINI_API_KEY)
    self.gemini_model = self.settings.GEMINI_EMBEDDING_MODEL  # "gemini-embedding-001"
```

Two embedding clients are set up: OpenAI as primary, Gemini as fallback.
The API keys come from `get_settings()` which reads your `.env` file.

```python
def embed_text(self, text: str) -> List[float]:

    # --- Step 1: Check Redis cache ---
    cache_key = self._make_embedding_cache_key(text, self.openai_model)
    cached_embedding = self.cache.get(cache_key)
    if cached_embedding:
        return cached_embedding   # ← Return immediately, no API call!

    # --- Step 2: Call OpenAI ---
    try:
        response = self.openai_client.embeddings.create(
            input=[text],
            model=self.openai_model
        )
        embedding = response.data[0].embedding  # ← The list of floats
        self.cache.set(cache_key, embedding)    # ← Save for next time
        return embedding

    # --- Step 3: If OpenAI fails, try Gemini ---
    except Exception as e:
        logger.warning(f"OpenAI failed, falling back to Gemini: {e}")
        result = self.gemini_client.models.embed_content(...)
        return list(result.embeddings[0].values)
```

**The cache key:**
```python
def _make_embedding_cache_key(self, text: str, model: str) -> str:
    return self.cache.make_key("embedding", {"text": text, "model": model})
    # Produces → "embedding:sha256(json({text, model}))"
```

The same query text always produces the same cache key, so Redis can
serve repeat queries instantly.

---

## File 6: `app/infrastructure/cache.py` — The Redis Cache

This service is the "memory" layer.

```python
def __init__(self):
    self.settings = get_settings()
    self.redis_client: Optional[redis.Redis] = None
    self.enabled = self.settings.CACHE_ENABLED   # from .env

    if self.enabled:
        self._connect()
```

```python
def _connect(self) -> None:
    try:
        self.redis_client = redis.from_url(
            self.settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=2   # ← Only wait 2 seconds
        )
        self.redis_client.ping()       # ← Test connection immediately
        logger.info("Connected to Redis")
    except (redis.ConnectionError, redis.TimeoutError) as e:
        logger.warning(f"Redis unavailable: {e}. Caching disabled.")
        self.enabled = False           # ← Graceful fallback!
        self.redis_client = None
```

**The key design: graceful degradation.**
If Redis is down, `self.enabled` is set to `False`. Every `get()` and
`set()` call checks `if not self.enabled` and returns `None`/`False`
immediately. The application keeps running — just without caching.

```python
def make_key(self, namespace: str, payload: dict) -> str:
    serialized_payload = json.dumps(payload, sort_keys=True)
    payload_hash = hashlib.sha256(serialized_payload.encode()).hexdigest()
    return f"{namespace}:{payload_hash}"
```

`sort_keys=True` is subtle but important: `{"text": "hi", "model": "x"}`
and `{"model": "x", "text": "hi"}` are the same thing semantically, and
`sort_keys` ensures they both produce the exact same hash.

```python
def get(self, key: str) -> Optional[Any]:
    if not self.enabled or not self.redis_client:
        return None          # ← Cache disabled → always a "miss"

    value = self.redis_client.get(key)
    if value:
        return json.loads(value)   # ← Redis stores strings, we stored JSON
    return None

def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
    if not self.enabled or not self.redis_client:
        return False

    serialized_value = json.dumps(value)
    expiry = ttl if ttl is not None else self.default_ttl  # default: 3600s = 1 hour
    self.redis_client.set(key, serialized_value, ex=expiry)
    return True
```

Everything stored in Redis is serialized to JSON string because Redis
only stores strings. `json.dumps()` converts Python objects → string.
`json.loads()` converts string → Python objects.

---

## File 7: `app/infrastructure/vector_store.py` — ChromaDB

This service answers: **"Which books are most similar to this vector?"**

```python
def __init__(self):
    self.settings = get_settings()
    # Creates (or opens) a local folder at ./chroma_db
    self.client = chromadb.PersistentClient(path=self.settings.CHROMA_PERSIST_DIR)
    self.collection = self._get_or_create_collection()
```

`PersistentClient` means ChromaDB saves data to disk in `./chroma_db`.
Every time the app restarts, the data is still there.

```python
def _get_or_create_collection(self):
    return self.client.get_or_create_collection(
        name=self.settings.CHROMA_COLLECTION_NAME,   # "library_docs"
        metadata={"hnsw:space": "cosine"}            # ← Use cosine similarity
    )
```

A "collection" in ChromaDB is like a table in SQL. `get_or_create` means:
- If `"library_docs"` collection already exists → return it
- If it doesn't exist → create it and return it

`"hnsw:space": "cosine"` tells ChromaDB to use **cosine similarity** for
comparisons. Cosine similarity measures the *angle* between two vectors.
Two vectors pointing in the same direction = similar meaning.

```python
def search(self, query_embedding: List[float], top_k: int = 5) -> List[Dict]:
    results = self.collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["metadatas", "distances", "documents"]
    )

    formatted_results = []
    for i in range(len(results["ids"][0])):
        distance = results["distances"][0][i]
        similarity_score = 1.0 - distance   # ← Convert distance to similarity

        metadata = results["metadatas"][0][i]
        formatted_results.append({
            "id": results["ids"][0][i],
            "title": metadata["title"],
            ...
            "score": round(similarity_score, 4)
        })

    return formatted_results
```

**Distance vs Similarity:**
ChromaDB with cosine space returns **distance** (0 = identical, 1 = totally different).
We want **similarity** (1 = identical, 0 = totally different).
So `similarity = 1.0 - distance`.

---

## Putting It All Together — One Request, Start to Finish

```
Client: POST /search/books
        Body: { "query": "space exploration adventures", "limit": 3 }
         │
         ▼
FastAPI validates body using BookSearchRequest
  ✓ query = "space exploration adventures" (length 3-500: OK)
  ✓ limit = 3 (ge=1, le=20: OK)
         │
         ▼
FastAPI calls Depends(get_embedding_service)
  → @lru_cache → returns existing EmbeddingService singleton
FastAPI calls Depends(get_vector_store)
  → @lru_cache → returns existing ChromaVectorStore singleton
         │
         ▼
search_books() function runs:
  embedding_svc.embed_text("space exploration adventures")
    │
    ├─ make cache key → "embedding:sha256(...)"
    ├─ redis.get(key) → None (first time = miss)
    ├─ openai.embeddings.create(input=["space exploration adventures"])
    │   → [0.0024, -0.0183, 0.0941, ...] (1536 floats)
    └─ redis.set(key, embedding, ex=3600)
         │
         ▼
  vector_store.search(query_embedding=[...1536 floats...], top_k=3)
    │
    └─ chromadb.collection.query(...)
        → Returns 3 most similar books by cosine distance
        → Converts distance → similarity score
         │
         ▼
  [BookResult(**r) for r in raw_results]
    → Wraps each dict into a Pydantic model (validates types)
         │
         ▼
  return BookSearchResponse(results=books, total=3, query="space exploration...")
    → FastAPI serializes to JSON
         │
         ▼
Client receives:
{
  "query": "space exploration adventures",
  "total": 3,
  "results": [
    {
      "id": "book_001",
      "title": "The Starlight Voyager",
      "author": "Elena Vance",
      "genre": "Science Fiction",
      "year": 2024,
      "description": "A high-stakes space travel adventure...",
      "score": 0.9241
    },
    ...
  ]
}
```

---

## Summary: Why Each Layer Exists

| Layer | File | Purpose |
|---|---|---|
| **Router** | `search.py` | Map URL → function, validate request/response shape |
| **Models** | `models.py` | Define the exact shape of data in and out |
| **Dependencies** | `dependencies.py` | Create singletons, wire services together |
| **Service** | `embedding_service.py` | Business logic: convert text to a vector |
| **Infrastructure** | `cache.py` | Talk to Redis, abstract caching details |
| **Infrastructure** | `vector_store.py` | Talk to ChromaDB, abstract search details |
| **Config** | `config.py` | Read `.env` variables, share settings everywhere |

Each layer only knows about the layer below it. The router doesn't know
Redis exists. The embedding service doesn't know ChromaDB exists.
This separation makes each piece easy to test and replace independently.
