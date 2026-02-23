
from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config("DJANGO_SECRET_KEY", default="preview-service-secret-key-dev")
DEBUG = config("DEBUG", default=True, cast=bool)
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "rest_framework",
    "preview",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "preview_service.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": []},
    }
]

WSGI_APPLICATION = "preview_service.wsgi.application"

# No database
DATABASES = {}

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Redis — used ONLY for the circuit breaker
REDIS_URL = config("REDIS_URL", default="redis://redis:6379/2")

# How many failures before a domain's circuit opens
CIRCUIT_BREAKER_FAILURE_THRESHOLD = config("CB_FAILURE_THRESHOLD", default=5, cast=int)
# How long (seconds) the circuit stays open before auto-reset
CIRCUIT_BREAKER_COOLDOWN = config("CB_COOLDOWN", default=60, cast=int)

# httpx fetch timeout (seconds)
FETCH_TIMEOUT = config("FETCH_TIMEOUT", default=5, cast=int)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "[%(asctime)s] %(levelname)s [%(name)s] %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
            "level": "INFO",
        }
    },
    "loggers": {
        "preview": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "django": {"handlers": ["console"], "level": "WARNING", "propagate": False},
    },
}
