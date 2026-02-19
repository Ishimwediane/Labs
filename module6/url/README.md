# Module 6: URL Shortener with PostgreSQL & User Accounts

A URL shortener microservice with **PostgreSQL database** and **user account management**. Built with Django REST Framework and fully containerized with Docker.

## 🚀 Features

- **URL Shortening**: Convert long URLs into short, shareable links
- **Automatic Redirect**: Short URLs automatically redirect to original URLs
- **Database Optimization**: Efficient queries using `select_related` and `prefetch_related`
- **Analytics**: Built-in click tracking with database-level aggregation
- **REST API**: Clean RESTful API with proper HTTP status codes
- **API Documentation**: Interactive Swagger UI for testing endpoints
- **Docker Support**: Fully containerized with Docker Compose
- **Admin Panel**: Django admin interface for managing URLs

## 🛠️ Technology Stack

- **Framework**: Django 5.0 + Django REST Framework
- **Optimization**: Django ORM (select_related, prefetch_related, indexes)
- **API Documentation**: drf-spectacular (OpenAPI/Swagger)
- **Server**: Gunicorn (production)
- **Containerization**: Docker & Docker Compose
- **Database**: SQLite (default, easily switchable to PostgreSQL)

## 📋 Prerequisites

- Python 3.11+
- Docker & Docker Compose (for containerized setup)

## 🔧 Setup Instructions

### Option 1: Run with Docker (Recommended)

1. **Clone the repository**
   ```bash
   cd c:\Users\Amalitech\Desktop\amali\Labs\Labs\module5
   ```

2. **Build and start containers**
   ```bash
   docker-compose up --build
   ```

3. **Access the application**
   - API Documentation (Swagger): http://localhost:8000/api/schema/swagger-ui/
   - Django Admin: http://localhost:8000/admin/
   - API Endpoint: http://localhost:8000/api/shorten/

### Option 2: Run Locally (Without Docker)

1. **Create virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run migrations**
   ```bash
   cd url
   python manage.py migrate
   ```

4. **Create superuser** (optional, for admin access)
   ```bash
   python manage.py createsuperuser
   ```

5. **Start development server**
   ```bash
   python manage.py runserver
   ```

6. **Access the application**
   - Swagger UI: http://127.0.0.1:8000/api/schema/swagger-ui/
   - Admin: http://127.0.0.1:8000/admin/

## 📚 API Usage

### 1. Create Short URL

**Endpoint**: `POST /api/shorten/`

**Request Body**:
```json
{
  "original_url": "https://www.example.com"
}
```

## Quick Start

### Run with Docker (Recommended)

```bash
# Navigate to module
cd module6

# Start all services
docker-compose up -d

# Run migrations
docker exec -it url_shortener_web python manage.py migrate

# Create superuser (optional)
docker exec -it url_shortener_web python manage.py createsuperuser

# Access the app
# Swagger UI: http://localhost:8000/api/schema/swagger-ui/
# Admin: http://localhost:8000/admin/
```

### Run Locally (Without Docker)

```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Set up PostgreSQL (ensure it's running)
# Update .env with your PostgreSQL credentials

# Run migrations
cd url
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start server
python manage.py runserver

# Access: http://127.0.0.1:8000/api/schema/swagger-ui/
```

## Key Features

- **PostgreSQL Database**: Production-ready relational database
- **User Accounts**: Custom User model with registration
- **URL Ownership**: Each URL belongs to a user
- **Redis Caching**: Fast URL lookups
- **REST API**: Full CRUD operations
- **Swagger UI**: Interactive API documentation
- **Docker**: Complete containerization

## API Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/shorten/` | Create short URL | No |
| GET | `/{short_code}/` | Redirect to original URL | No |
| GET | `/api/schema/swagger-ui/` | API documentation | No |
| GET | `/admin/` | Admin panel | Yes (Staff) |

## Technology Stack

- **Framework**: Django 6.0 + Django REST Framework
- **Database**: PostgreSQL 15
- **Cache**: Redis 7
- **API Docs**: drf-spectacular
- **Containerization**: Docker & Docker Compose

## Project Structure

```
module6/
├── url/
│   ├── accounts/          # User management app
│   │   ├── models.py      # Custom User model
│   │   └── admin.py
│   ├── api/               # REST API endpoints
│   │   ├── views.py
│   │   ├── serializers.py
│   │   └── urls.py
│   ├── shortener/         # Core URL shortening logic
│   │   ├── models.py      # URL model
│   │   └── services.py
│   └── url/               # Project settings
│       └── settings.py    # PostgreSQL config
├── docker-compose.yml     # Orchestration
└── Dockerfile
```

## Database Inspection

```bash
# Connect to PostgreSQL
docker exec -it url_shortener_postgres psql -U postgres -d module6_db

# View users
SELECT id, username, email FROM accounts_user;

# View URLs with owners
SELECT url.short_url, url.original_url, u.username
FROM shortener_url url
JOIN accounts_user u ON url.owner_id = u.id;

# Exit
\q
```

## Troubleshooting

**Database connection error:**
```bash
cd url
python manage.py makemigrations
python manage.py migrate
```

## 📝 Development Notes

### How It Works
1. User submits a long URL via POST request
2. Service generates a unique 6-character short code
3. URL mapping is stored in both Redis (primary) and SQLite (backup)
4. Short code is cached in Redis for ultra-fast lookups
5. When user visits short URL, Redis provides instant redirect

### Key Design Decisions
- **Database Indexing**: `db_index=True` on critical fields for fast lookups
- **Query Optimization**: Preventing N+1 problems with eager loading
- **Database Aggregation**: Using `annotate()` for efficient analytics calculation
- **RESTful Design**: Proper HTTP methods and status codes
- **Docker**: Easy deployment and consistent environments


## 🚢 Production Deployment

For production deployment:

1. Update `.env` with production values:
   - Set `DEBUG=False`
   - Use strong `SECRET_KEY`
   - Configure `ALLOWED_HOSTS`

2. Use production Docker target:
   ```bash
   docker-compose -f docker-compose.prod.yml up
   ```

3. Use PostgreSQL instead of SQLite (recommended)

4. Set up proper reverse proxy (nginx)

## 📄 License

This project is created for educational purposes as part of the Python Backend course.

## 👨‍💻 Author

Created as Lab 1: URL Shortener Microservice

---

**Module 6 Complete!**   *Next: Module 7 - Authentication & Authorization*
