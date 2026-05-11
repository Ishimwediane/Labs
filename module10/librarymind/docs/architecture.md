# LibraryMind Architecture

This document visualizes the internal architecture of the LibraryMind project, showcasing how the configuration, AI providers, and infrastructure components interact to provide a resilient semantic search experience.

```mermaid
flowchart TB
    %% Styling
    classDef setup fill:#f9f,stroke:#333,stroke-width:2px;
    classDef ai fill:#bbf,stroke:#333,stroke-width:2px;
    classDef infra fill:#bfb,stroke:#333,stroke-width:2px;
    classDef storage fill:#fdb,stroke:#333,stroke-width:2px;

    subgraph P0["Part 0: Configuration & Environment"]
        direction LR
        env[".env"]
        config["app/config.py"]
        env --> config
    end

    subgraph P1["Part 1: The AI Provider Layer"]
        base["base.py (Interface)"]
        openai["openai_provider.py"]
        claude["anthropic_provider.py"]
        gemini["gemini_provider.py"]
        resilient["resilient_service.py"]

        base --> openai & claude & gemini
        openai & claude & gemini -.->|Fallbacks| resilient
    end

    subgraph P2["Part 2: Support Infrastructure"]
        cache["cache.py (Redis)"]
        limiter["rate_limiter.py"]
        usage["usage_tracker.py"]
        
        cache --- keys["Deterministic Keys"]
    end

    subgraph P3["Part 3: Knowledge Base & RAG"]
        books["data/books.json"]
        seed["scripts/seed_books.py"]
        embed["embedding_service.py"]
        chroma["vector_store.py (ChromaDB)"]
        
        books --> seed
        seed --> embed --> chroma
    end

    %% Global Connections
    config --> P1
    config --> P2
    config --> P3

    P2 --> P1
    P1 -->|Generate Response| RAG["Final User Answer"]
    chroma -->|Relevant Context| RAG

    %% Class Assignments
    class env,config setup;
    class base,openai,claude,gemini,resilient ai;
    class cache,limiter,usage infra;
    class books,seed,embed,chroma storage;
```

## Component Breakdown

### Part 0: Configuration
Handles the loading and validation of environment variables using Pydantic. It ensures the app doesn't start unless the required API keys and settings are present.

### Part 1: AI Layer
A resilient multi-provider setup. It implements an abstract base class for AI providers, allowing the application to switch between OpenAI, Anthropic, and Gemini seamlessly if one fails or hits a quota limit.

### Part 2: Infrastructure
The "Utility" layer:
- **Cache**: Reduces API costs and latency by storing deterministic results in Redis.
- **Rate Limiter**: Implements a Token Bucket algorithm to prevent API abuse.
- **Usage Tracker**: Estimates USD costs and token usage in real-time.

### Part 3: Knowledge Base
The search engine:
- **ChromaDB**: A vector database for storing book embeddings.
- **Embedding Service**: Converts raw book descriptions into semantic vectors.
- **Seed Script**: Automates the ingestion of the `books.json` dataset.
