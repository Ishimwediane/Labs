from typing import Any, Optional
from pydantic import BaseModel, Field



# POST /search/books

class BookSearchRequest(BaseModel):
    """Body for semantic book search."""

    query: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="The search query (e.g. 'dystopian novels about survival').",
        examples=["science fiction books about space exploration"],
    )
    limit: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of results to return (1–20).",
    )


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
    total: int = Field(description="Number of results returned.")
    query: str = Field(description="The original search query echoed back.")



# POST /search/ask


class AskRequest(BaseModel):
    """Body for RAG-powered question answering."""

    question: str = Field(
        ...,
        min_length=5,
        max_length=500,
        description="A natural-language question about the library catalogue.",
        examples=["Which books deal with artificial intelligence ethics?"],
    )


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

    conversation_id: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description=(
            "A unique ID for this chat session. Use a UUID. "
            "The same ID must be sent on every turn to maintain memory."
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
    conversation_id: str = Field(description="The conversation ID echoed back.")



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
    department: str = Field(
        description="Suggested handling department (e.g. 'Membership', 'IT Support')."
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
