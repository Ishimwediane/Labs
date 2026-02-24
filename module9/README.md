# Module 9: Microservices Essentials - Distributed URL Shortener

This project implements a master-worker microservices architecture. It decouples the core URL management from the external scraping logic, ensuring high performance and system resiliency.

## 🏗️ Full-Stack Architecture

```mermaid
graph TD
    User([User / React Frontend]) -->|API Port :8002| Web[URL Service]
    Web -->|Store| Postgres[(PostgreSQL :5433)]
    Web -->|Queue Task| Redis[(Redis :6380)]
    
    Worker[Celery Worker] -->|Listen| Redis
    Worker -->|Fetch Internal :8001| Preview[Preview Service]
    Preview -->|Scrape| WebInternet((Internet))
    
    Worker -->|Save Metadata| Postgres
    Beat[Celery Beat] -->|Cron| Redis
    
    style Web fill:#4CAF50,stroke:#333
    style Preview fill:#2196F3,stroke:#333
    style Worker fill:#FF9800,stroke:#333
```

## 📁 Repository Structure

```text
module9/
├── url/               # The "Orchestrator" (Users, Shortening, Analytics)
├── preview_service/   # The "Scout" (Stateless Metadata Scraper)
└── docker-compose.yml # The "Master Config" (Starts 6 containers)
```

## 🚀 How to Start with Docker

### 1. Launch the Cluster
```powershell
# Navigate to the root module9 folder
docker-compose up -d --build
```

### 2. Prepare the Environment
```powershell
# Run migrations inside the Web container
docker exec -it m9_web python manage.py migrate

# Create your primary admin
docker exec -it m9_web python manage.py createsuperuser
```

### 3. Master Access Table
| Resource | URL |
|----------|-----|
| **Main API Swagger** | [http://localhost:8002/api/schema/swagger-ui/](http://localhost:8002/api/schema/swagger-ui/) |
| **Preview API Swagger** | [http://localhost:8001/schema/swagger-ui/](http://localhost:8001/schema/swagger-ui/) |
| **Admin Panel** | [http://localhost:8002/admin/](http://localhost:8002/admin/) |
| **Redis Explorer** | Connect to `localhost:6380` |

---

## 📡 API Overview (JSON Examples)

### Create & Scrape Flow
1. **Request** (`POST :8002/api/v1/urls/`):
   ```json
   {"original_url": "https://github.com"}
   ```
2. **Internal Response** (Preview Service `:8001`):
   ```json
   {"title": "GitHub", "description": "Build software...", "favicon": "..."}
   ```

## 🌐 Frontend & CORS
The system is ready for a React/Vue frontend out of the box. 
- **CORS Headers**: Handled by `django-cors-headers` in the URL service.
- **Access Control**: Configure `CORS_ALLOWED_ORIGINS` in `url/settings.py` to add your frontend domain (e.g., `http://localhost:3000`).

## 🛠️ Essential Docker Commands
- `docker-compose logs -f`: View live logs for all services.
- `docker-compose restart worker`: Restart specifically the scraper worker.
- `docker-compose down -v`: Complete reset (wipes the database).
