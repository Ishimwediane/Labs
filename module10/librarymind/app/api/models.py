from enum import Enum
from typing import Any, List, Optional
from pydantic import BaseModel, Field, field_validator



# POST /search/books

class BookSearchRequest(BaseModel):
    """Body for semantic book search with optional filters.

    Pagination is controlled via query parameters (?page=&limit=) on the endpoint,
    not inside this body — keeping the body focused on what you are searching for.
    """

    query: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="The search query (e.g. 'dystopian novels about survival').",
    )

    # --- Optional Filters ---
    # These narrow the results AFTER semantic search is done.
    genre: Optional[str] = Field(
        default=None,
        description="Filter by exact genre (e.g. 'Science Fiction', 'Fantasy', 'Thriller').",
    )
    author: Optional[str] = Field(
        default=None,
        description="Filter by author name (partial match, case-insensitive).",
    )
    year_min: Optional[int] = Field(
        default=None,
        ge=0,
        description="Only return books published from this year onwards.",
    )
    year_max: Optional[int] = Field(
        default=None,
        ge=0,
        description="Only return books published up to and including this year.",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "query": "science fiction books about space exploration",
                "genre": None,
                "author": None,
                "year_min": None,
                "year_max": None,
            }
        }
    }



class BookResult(BaseModel):
    """A single book returned by a search."""

    id: str
    title: str
    author: str
    genre: str
    year: int
    description: str
    score: float = Field(description="Cosine similarity score (0.0–1.0, higher is better).")


class BookSearchResponse(BaseModel):
    """Response body for POST /search/books."""

    results: list[BookResult]
    total: int = Field(description="Number of results in this page.")
    total_matches: int = Field(description="Total books matching query + filters (before pagination).")
    total_pages: int = Field(description="Total number of pages available.")
    page: int = Field(description="The current page number.")
    limit: int = Field(description="The page size that was requested.")
    query: str = Field(description="The original search query echoed back.")



# POST /search/ask


class AskRequest(BaseModel):
    """Body for RAG-powered question answering with optional filters."""

    question: str = Field(
        ...,
        min_length=5,
        max_length=500,
        description="A natural-language question about the library catalogue.",
    )

    # --- Optional Filters ---
    # These narrow the CONTEXT books the LLM sees before generating the answer.
    # e.g. genre='Fantasy' means the AI will only answer using Fantasy books.
    genre: Optional[str] = Field(
        default=None,
        description="Restrict context to books of this genre (e.g. 'Cyberpunk').",
    )
    year_min: Optional[int] = Field(
        default=None,
        ge=0,
        description="Only use books published from this year onwards as context.",
    )
    year_max: Optional[int] = Field(
        default=None,
        ge=0,
        description="Only use books published up to this year as context.",
    )

    # This sets the pre-filled example in Swagger UI.
    model_config = {
        "json_schema_extra": {
            "example": {
                "question": "Which science fiction books deal with space travel?",
                "genre": None,
                "year_min": None,
                "year_max": None
            }
        }
    }


class AskResponse(BaseModel):
    """Response body for POST /search/ask."""

    answer: str = Field(description="The AI-generated answer grounded in the catalogue.")
    sources: list[dict[str, Any]] = Field(
        description="Books used as grounding context. Each has title, author, score."
    )
    cached: bool = Field(description="True if this answer was served from the Redis cache.")



# POST /chat


class ChatRequest(BaseModel):
    """Body for a single chatbot turn."""

    conversation_id: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=128,
        description=(
            "A unique ID for this chat session. "
            "If omitted, the server auto-generates a new UUID and returns it. "
            "Send the same ID on every subsequent turn to maintain memory."
        ),
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="The patron's message for this turn.",
        examples=["Can you recommend a mystery novel set in Paris?"],
    )


class ChatResponse(BaseModel):
    """Response body for POST /chat."""

    reply: str = Field(description="The AI librarian's response.")
    sources: list[dict[str, Any]] = Field(
        description="Books referenced in this reply (may be empty for greetings)."
    )
    conversation_id: str = Field(
        description="The conversation ID for this session. Save this and send it on the next turn."
    )


# ── Session / History models ──────────────────────────────────────────────


class SessionSummary(BaseModel):
    """Metadata summary for a single active conversation session."""

    conversation_id: str = Field(description="Unique session identifier.")
    message_count: int = Field(description="Total number of messages (user + assistant) stored.")
    messages_remaining: int = Field(
        description="How many more messages can be added before the session cap is hit."
    )
    last_role: Optional[str] = Field(
        default=None,
        description="Role of the last message: 'user' or 'assistant'.",
    )
    last_message_preview: Optional[str] = Field(
        default=None,
        description="First 80 characters of the most recent message.",
    )
    last_active: Optional[str] = Field(
        default=None,
        description="ISO-8601 timestamp of the most recent message.",
    )


class SessionListResponse(BaseModel):
    """Response body for GET /chat/sessions."""

    sessions: List[SessionSummary] = Field(description="Paginated list of active sessions.")
    total: int = Field(description="Total number of active sessions (before pagination).")
    page: int = Field(description="Current page number.")
    limit: int = Field(description="Page size requested.")
    total_pages: int = Field(description="Total number of pages available.")
    storage_backend: str = Field(description="Active storage backend: 'redis' or 'memory'.")


class SessionHistoryResponse(BaseModel):
    """Response body for GET /chat/sessions/{conversation_id}."""

    conversation_id: str = Field(description="Unique session identifier.")
    messages: List[dict] = Field(description="Full ordered message history (oldest first).")
    message_count: int = Field(description="Total number of messages stored.")
    messages_remaining: int = Field(
        description="How many more messages can be added before the session cap is hit."
    )
    storage_backend: str = Field(description="Active storage backend: 'redis' or 'memory'.")


class SessionResetResponse(BaseModel):
    """Response body for POST /chat/sessions/{conversation_id}/reset."""

    conversation_id: str = Field(description="The session that was reset.")
    message: str = Field(
        description="Confirmation message.",
        default="Session history cleared. The session ID is still valid — send messages to continue.",
    )
    messages_remaining: int = Field(
        description="Messages available after reset (equals the full session cap)."
    )






# POST /classify/ticket


class TicketRequest(BaseModel):
    """Body for support ticket classification."""

    ticket_text: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="The raw text of the support ticket to classify.",
        examples=[
            "My library card isn't working at the self-checkout. "
            "I've been trying for 20 minutes and I'm very frustrated."
        ],
    )

    @field_validator("ticket_text")
    @classmethod
    def validate_ticket_text(cls, v: str) -> str:
        if not isinstance(v, str):
            raise ValueError("ticket_text must be a string")
        stripped = v.strip()
        if len(stripped) < 10:
            raise ValueError("ticket_text must contain at least 10 non-whitespace characters")
        return stripped


class LibraryDepartment(str, Enum):
    """Predefined library departments for support tickets."""

    CIRCULATION = "Circulation"
    IT_SUPPORT = "IT Support"
    COLLECTIONS = "Collections"
    REFERENCE = "Reference"
    MEMBERSHIP = "Membership"
    BILLING = "Billing"
    ADMINISTRATION = "Administration"


class TicketClassificationResponse(BaseModel):
    """Response body for POST /classify/ticket."""

    category: str = Field(
        description="Ticket category: account | borrowing | technical | complaint | suggestion | general"
    )
    priority: str = Field(
        description="Urgency level: low | medium | high | urgent"
    )
    sentiment: str = Field(
        description="Patron sentiment: positive | neutral | negative"
    )
    department: LibraryDepartment = Field(
        description="Predefined library department."
    )
    summary: str = Field(
        description="One-sentence summary of the ticket."
    )



# POST /summarise/reviews

class ReviewSummarisationRequest(BaseModel):
    """Body for review summarisation."""

    reviews: list[str] = Field(
        ...,
        min_length=1,
        description="A list of 1–50 review strings to summarise holistically.",
        examples=[
            [
                "Loved the characters, the plot felt slow.",
                "A masterpiece. Could not put it down.",
                "Good book but the ending felt rushed.",
            ]
        ],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "reviews": [
                        "Loved the characters, the plot felt slow.",
                        "A masterpiece. Could not put it down.",
                        "Good book but the ending felt rushed.",
                    ]
                }
            ]
        }
    }


class ReviewSummarisationResponse(BaseModel):
    """Response body for POST /summarise/reviews."""

    overall_sentiment: str = Field(
        description="Cross-review sentiment: positive | negative | mixed"
    )
    average_rating: float = Field(
        description="Estimated average rating out of 5.0."
    )
    key_themes: list[str] = Field(
        description="Main themes that appear across the reviews."
    )
    praise: list[str] = Field(
        description="Things readers consistently liked."
    )
    criticism: list[str] = Field(
        description="Things readers consistently disliked."
    )
    recommendation: str = Field(
        description="One-sentence recommendation for prospective readers."
    )



# GET /health


class HealthResponse(BaseModel):
    """Response body for GET /health."""

    status: str = Field(description="Application status. Always 'ok' when reachable.")
    environment: str = Field(description="Deployment environment (development / production).")
    primary_provider: str = Field(description="Active AI provider (openai / anthropic / gemini).")
    total_requests: int = Field(description="Total AI calls made since server start.")
    daily_cost_usd: float = Field(description="Estimated AI spend today in USD.")



# Shared error shapes ( documenting them helps Swagger UI users)


class ErrorDetail(BaseModel):
    detail: str


class ValidationErrorResponse(BaseModel):
    detail: list[dict[str, Any]]
