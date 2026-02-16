# Module 7: URL Shortener with Authentication & Authorization

A production-ready URL shortener microservice featuring **JWT authentication**, **role-based access control (RBAC)**, **tiered user system**, and **Redis caching**. Built with Django REST Framework and fully containerized with Docker.

##  Features

### Authentication & Security
- **JWT Authentication**: Secure token-based authentication with access and refresh tokens
- **User Registration**: Email validation and secure password hashing
- **Rate Limiting**: Throttling on login endpoint (5 attempts/minute) to prevent brute force attacks
- **Password Security**: Django's PBKDF2 password hashing with salt

### Authorization & RBAC
- **Custom Permissions**: `IsOwnerOrReadOnly` - users can only modify their own URLs
- **Tiered User System**: Free and Premium user tiers with different capabilities
- **Business Logic Enforcement**: Automatic tier-based feature restrictions

### URL Shortening
- **Smart URL Generation**: Automatic short code generation with collision detection
- **Custom Aliases**: Premium users can set custom short codes
- **Fast Redirects**: Redis-cached URL lookups for instant redirection
- **Click Tracking**: Record IP address, user agent, and referrer for each click
- **Analytics**: Premium users get detailed click statistics by country

### Tier-Based Features

| Feature | Free Users | Premium Users |
|---------|-----------|---------------|
| Max Active URLs | 10 | Unlimited |
| Custom Aliases | ❌ | ✅ |
| Detailed Analytics | ❌ | ✅ |
| Click Tracking | ✅ | ✅ |
| URL Redirection | ✅ | ✅ |

## Technology Stack

- **Framework**: Django 5.0.1 + Django REST Framework 3.14
- **Authentication**: djangorestframework-simplejwt 5.3
- **Database**: PostgreSQL 15 (Alpine)
- **Cache**: Redis 7 (Alpine)
- **API Documentation**: drf-spectacular 0.27 (OpenAPI/Swagger)
- **Containerization**: Docker & Docker Compose
- **Python**: 3.11

##  Prerequisites

- Docker Desktop installed and running
- Docker Compose (included with Docker Desktop)
- Git (for cloning the repository)

##  Quick Start

### 1. Clone and Navigate

```bash
cd c:\Users\Amalitech\Desktop\amali\Labs\Labs\module7\url
```

### 2. Configure Environment

Create `.env` file (or verify it exists):

```bash
POSTGRES_DB=module7_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=db
POSTGRES_PORT=5432

SECRET_KEY=django-insecure-super-secret-key
DEBUG=True
REDIS_LOCATION=redis://redis:6379/1
```

### 3. Start Services

```bash
# Start all containers (PostgreSQL, Redis, Django)
docker-compose up -d

# Check containers are running
docker-compose ps
```

### 4. Run Migrations

```bash
# Apply database migrations
docker exec -it url_shortener_web python manage.py migrate

# Create superuser (optional, for admin access)
docker exec -it url_shortener_web python manage.py createsuperuser
```

### 5. Access the Application

- **Swagger UI**: http://localhost:8000/api/schema/swagger-ui/
- **ReDoc**: http://localhost:8000/api/schema/redoc/
- **Admin Panel**: http://localhost:8000/admin/
- **API Schema**: http://localhost:8000/api/schema/

##  API Documentation

### Authentication Endpoints

#### Register User
```http
POST /accounts/register/
Content-Type: application/json

{
  "username": "testuser",
  "email": "user@example.com",
  "password": "SecurePass123!",
  "password_confirm": "SecurePass123!",
  "is_premium": false
}
```

**Response (201 Created)**:
```json
{
  "username": "testuser",
  "email": "user@example.com",
  "is_premium": false
}
```

#### Login
```http
POST /accounts/login/
Content-Type: application/json

{
  "username": "testuser",
  "password": "SecurePass123!"
}
```

**Response (200 OK)**:
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

#### Refresh Token
```http
POST /accounts/token/refresh/
Content-Type: application/json

{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### URL Management Endpoints

#### Create Short URL (Requires Authentication)
```http
POST /api/urls/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "original_url": "https://www.example.com",
  "custom_alias": "my-link"  // Optional, premium only
}
```

**Response (201 Created)**:
```json
{
  "id": 1,
  "original_url": "https://www.example.com",
  "short_url": "my-link",
  "short_link": "http://localhost:8000/my-link/",
  "click_count": 0,
  "detailed_stats": null,  // Premium users see click data here
  "created_at": "2026-02-16T10:00:00Z"
}
```

#### Redirect to Original URL (Public)
```http
GET /{short_code}/
```

**Response**: 302 Redirect to original URL

##  Testing Guide

### Using Swagger UI

1. **Open Swagger UI**: http://localhost:8000/api/schema/swagger-ui/

2. **Register a User**:
   - Find `POST /accounts/register/`
   - Click "Try it out"
   - Enter user details
   - Execute

3. **Login**:
   - Find `POST /accounts/login/`
   - Enter credentials
   - Copy the `access` token from response

4. **Authorize**:
   - Click green "Authorize" button at top
   - Enter: `Bearer <your_access_token>`
   - Click "Authorize" then "Close"

5. **Create URLs**:
   - Find `POST /api/urls/`
   - Click "Try it out"
   - Enter URL data
   - Execute

6. **Test Redirect**:
   - Copy `short_link` from response
   - Open in browser
   - Should redirect to original URL

### Testing Business Logic

**Free User Limits**:
```bash
# Create 11 URLs as free user
# 11th URL should fail with: "Free users can only create up to 10 active URLs."
```

**Premium Features**:
```bash
# Try custom alias as free user - should fail
# Try custom alias as premium user - should work
# Premium users see detailed_stats, free users see null
```

**Rate Limiting**:
```bash
# Try 6 failed logins within 1 minute
# 6th attempt should return: 429 Too Many Requests
```

## Database Inspection

### Connect to PostgreSQL

```bash
docker exec -it url_shortener_postgres psql -U postgres -d module7_db
```

### Useful Queries

```sql
-- View all users
SELECT id, username, email, is_premium, tier FROM accounts_user;

-- View all URLs with owner info
SELECT url.short_url, url.original_url, u.username, u.is_premium
FROM shortener_url url
JOIN accounts_user u ON url.owner_id = u.id;

-- Count URLs per user
SELECT u.username, COUNT(url.id) as url_count
FROM accounts_user u
LEFT JOIN shortener_url url ON u.id = url.owner_id
GROUP BY u.username;

-- View click tracking data
SELECT url.short_url, c.country, COUNT(*) as clicks
FROM shortener_click c
JOIN shortener_url url ON c.url_id = url.id
GROUP BY url.short_url, c.country;

-- Exit
\q
```

##  Redis Inspection

### Connect to Redis

```bash
docker exec -it url_shortener_redis redis-cli
```

### Useful Commands

```redis
# Test connection
PING

# View all cached URLs
KEYS url:*

# Get cached URL
GET url:abc123

# View rate limiting data
KEYS login_throttle:*
GET login_throttle:testuser

# Monitor real-time commands
MONITOR

# Exit
EXIT
```

## Project Structure

```
module7/url/
├── accounts/                    # Authentication app
│   ├── models.py               # Custom User model
│   ├── serializers.py          # Login, Register serializers
│   ├── views.py                # Login, Register views
│   ├── urls.py                 # Auth endpoints
│   └── throttling.py           # Rate limiting
├── api/                        # API app
│   ├── serializers.py          # URL serializers
│   ├── views.py                # URL CRUD views
│   ├── urls.py                 # API endpoints
│   └── permissions.py          # Custom permissions
├── shortener/                  # Core business logic
│   ├── models.py               # Url, Click, Tag models
│   ├── services.py             # UrlShortenerService
│   └── admin.py                # Admin configuration
├── url/                        # Project settings
│   ├── settings.py             # Django configuration
│   └── urls.py                 # Main URL routing
├── .env                        # Environment variables
├── docker-compose.yml          # Docker orchestration
├── Dockerfile                  # Docker image
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## API Endpoints Summary

| Method | Endpoint | Auth Required | Description |
|--------|----------|---------------|-------------|
| POST | `/accounts/register/` | ❌ | Register new user |
| POST | `/accounts/login/` | ❌ | Login and get JWT tokens |
| POST | `/accounts/token/refresh/` | ❌ | Refresh access token |
| POST | `/api/urls/` | ✅ | Create short URL |
| GET | `/{short_code}/` | ❌ | Redirect to original URL |
| GET | `/api/schema/` | ❌ | OpenAPI schema (JSON) |
| GET | `/api/schema/swagger-ui/` | ❌ | Interactive API docs |
| GET | `/admin/` | ✅ (Staff) | Django admin panel |

## Troubleshooting

### Containers Won't Start

```bash
# Check logs
docker-compose logs web
docker-compose logs db
docker-compose logs redis

# Restart services
docker-compose restart

# Full reset
docker-compose down -v
docker-compose up -d
```

### Database Connection Error

```bash
# Wait for database to be ready
docker-compose up -d db
timeout /t 10
docker-compose up -d web
```

### Redis Connection Error

```bash
# Verify REDIS_LOCATION in .env
cat .env | grep REDIS

# Should be: redis://redis:6379/1
# NOT: redis://127.0.0.1:6379/1
```

### Swagger UI Not Loading

```bash
# Check for serializer errors
docker-compose logs web | grep -i error

# Restart web container
docker-compose restart web
```

##  Security Features

- **JWT Tokens**: Secure, stateless authentication
- **Password Hashing**: PBKDF2 with salt (Django default)
- **Rate Limiting**: Prevents brute force attacks
- **Input Validation**: URL format validation
- **Permission Classes**: Owner-based access control
- **CORS Ready**: Configurable for production

## Production Deployment

### Environment Variables

Update `.env` for production:

```bash
SECRET_KEY=<generate-strong-secret-key>
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Use strong database credentials
POSTGRES_PASSWORD=<strong-password>

# Configure Redis with password
REDIS_LOCATION=redis://:password@redis:6379/1
```

### Docker Production Build

```bash
# Build production image
docker-compose -f docker-compose.prod.yml build

# Start production services
docker-compose -f docker-compose.prod.yml up -d
```

### Recommended Production Setup

1. Use **PostgreSQL** (already configured)
2. Use **Redis** with password authentication
3. Set up **nginx** as reverse proxy
4. Enable **HTTPS** with SSL certificates
5. Configure **CORS** for frontend domains
6. Set up **logging** and monitoring
7. Use **Gunicorn** or **uWSGI** instead of runserver

## Performance

- **Redis Caching**: 100x faster URL lookups vs database queries
- **Connection Pooling**: Efficient database connections
- **Lazy Loading**: Optimized queries with `select_related`
- **Indexed Fields**: Fast lookups on `short_url` and `owner_id`

##  License

This project is created for educational purposes as part of the Python Backend Development course - Module 7: Authentication & Authorization.

##  Author

**Ishimwe Diane**
- GitHub: [@Ishimwediane](https://github.com/Ishimwediane)

##  Learning Outcomes

By completing this module, you've learned:
- JWT authentication implementation
- Role-based access control (RBAC)
- Custom Django permissions
- Business logic enforcement
- Redis caching strategies
- Rate limiting and throttling
- Docker containerization
- API documentation with Swagger
- Security best practices

---

**Module 7 Complete! 🎉**
