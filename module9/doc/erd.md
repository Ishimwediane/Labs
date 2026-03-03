# Entity Relationship Diagram (ERD)

This document outlines the database schema for the Distributed URL Shortener service.

## Diagram

```mermaid
erDiagram
    USER ||--o{ URL : "owns"
    USER {
        int id PK
        string username
        string email
        boolean is_premium "Default: False"
        string tier "Choices: free, pro, enterprise"
    }
    
    URL ||--o{ CLICK : "receives"
    URL }o--o{ TAG : "categorized by"
    URL {
        int id PK
        string original_url
        string short_url "Unique Index"
        datetime created_at
        int click_count "Default: 0"
        boolean is_active "Default: True"
        datetime expires_at "Nullable"
        string custom_alias "Unique, Nullable"
        string title "Nullable (From Preview Service)"
        string description "Nullable (From Preview Service)"
        string favicon "Nullable (From Preview Service)"
        int owner_id FK
    }
    
    CLICK {
        int id PK
        string ip_address
        string user_agent
        string country "Nullable"
        string city "Nullable"
        string referer "Nullable"
        datetime created_at
        int url_id FK
    }
    
    TAG {
        int id PK
        string name "Unique"
    }
```

## Description of Entities

1. **USER**: Represents the application users who can create and manage their shortened URLs. Users have tiers (free, pro, enterprise) which can dictate feature access limits (like custom aliases).
2. **URL**: The core entity storing shortened link information. Includes raw URL, short code, and scraped metadata (title, description, favicon).
3. **CLICK**: Represents a single navigation event through a shortened link. Captures granular analytics like IP, location, and user agent.
4. **TAG**: Used to group and filter URLs. Has a Many-to-Many relationship with URLs.
