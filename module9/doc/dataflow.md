# Dataflow Diagrams

This document illustrates how data moves through the Distrbuted URL Shortener system during key operations.

## 1. URL Creation & Background Processing Flow

When a user submits a long URL to be shortened, the system immediately returns a short link while deferring the heavy lifting (web scraping) to background workers.

```mermaid
sequenceDiagram
    participant C as Client
    participant API as URL API Service
    participant DB as PostgreSQL
    participant R as Redis (Task Queue)
    participant W as Celery Worker
    participant P as Preview Service
    participant Ext as Target Website

    C->>API: POST /api/v1/urls/ {original_url}
    API->>DB: Insert new URL record (short_code)
    API->>R: Enqueue scrape task (url_id, original_url)
    API-->>C: 201 Created {short_url}
    
    Note over R, W: Asynchronous Background Process
    R-->>W: Consume scrape task
    W->>P: GET /scrape?url={original_url}
    P->>Ext: HTTP GET
    Ext-->>P: HTML Content
    P-->>W: Extracted Metadata (Title, Desc, Favicon)
    W->>DB: Update URL record with metadata
```

## 2. Redirection & Click Tracking Flow

When a user clicks on a shortened link, the system captures analytic data before sending them to the destination.

```mermaid
sequenceDiagram
    participant U as User Browser
    participant API as URL API Service
    participant DB as PostgreSQL

    U->>API: GET /{short_code}
    API->>DB: Lookup URL by short_code
    
    alt URL not found or inactive
        API-->>U: 404 Not Found
    else URL is active
        API->>DB: Insert Click (IP, User Agent, Location)
        API->>DB: Increment URL click_count
        API-->>U: 302 Redirect to original_url
        U->>Target Website: Navigate
    end
```

## Data Protection Mechanisms

### Circuit Breaker
If the `Preview Service` fails to scrape a target website 5 times consecutively, the Worker pushes a `blocked:{domain}` key to Redis. Subsequent tasks for that domain are skipped for 10 minutes to conserve resources and prevent cascading failures.
