"""Django settings for the FarmHub project."""

from datetime import timedelta
from pathlib import Path

import environ

# ==================================================
# Base
# ==================================================

BASE_DIR = Path(__file__).resolve().parent.parent


# ==================================================
# Environment
# ==================================================

env = environ.Env(
    DEBUG=(bool, True),
)

environ.Env.read_env(BASE_DIR / ".env", overwrite=True)


# ==================================================
# Security
# ==================================================

SECRET_KEY = env(
    "SECRET_KEY",
    default="django-insecure-change-me",
)

DEBUG = env.bool(
    "DEBUG",
    default=True,
)

ALLOWED_HOSTS = env.list(
    "ALLOWED_HOSTS",
    default=[
        "localhost",
        "127.0.0.1",
        "testserver",
    ],
)


# ==================================================
# Application Definition
# ==================================================

INSTALLED_APPS = [
    # ----------------------------------------------
    # Django
    # ----------------------------------------------
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # ----------------------------------------------
    # Third-party
    # ----------------------------------------------
    "corsheaders",
    "django_extensions",
    "django_filters",
    "drf_spectacular",
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    # ----------------------------------------------
    # FarmHub apps
    # ----------------------------------------------
    "apps.accounts.apps.AccountsConfig",
    "apps.farms.apps.FarmsConfig",
    "apps.farmers.apps.FarmersConfig",
    "apps.cattle.apps.CattleConfig",
    "apps.activities.apps.ActivitiesConfig",
    "apps.production.apps.ProductionConfig",
]


# ==================================================
# Middleware
# ==================================================

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# ==================================================
# URL Configuration
# ==================================================

ROOT_URLCONF = "config.urls"


# ==================================================
# Templates
# ==================================================

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


# ==================================================
# WSGI / ASGI
# ==================================================

WSGI_APPLICATION = "config.wsgi.application"

ASGI_APPLICATION = "config.asgi.application"


# ==================================================
# Database
# SQLite
# ==================================================

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# ==================================================
# Custom User Model
# ==================================================

AUTH_USER_MODEL = "accounts.User"


# ==================================================
# Password Validation
# ==================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": ("django.contrib.auth.password_validation.MinimumLengthValidator"),
    },
    {
        "NAME": ("django.contrib.auth.password_validation.CommonPasswordValidator"),
    },
    {
        "NAME": ("django.contrib.auth.password_validation.NumericPasswordValidator"),
    },
]


# ==================================================
# Internationalization
# ==================================================

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Asia/Dhaka"

USE_I18N = True

USE_TZ = True


# ==================================================
# Static Files
# ==================================================

STATIC_URL = "static/"


# ==================================================
# Default Primary Key
# ==================================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ==================================================
# CORS
# ==================================================

CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS",
    default=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
)


# ==================================================
# Django REST Framework
# ==================================================

REST_FRAMEWORK = {
    # ----------------------------------------------
    # Authentication
    # ----------------------------------------------
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    # ----------------------------------------------
    # Permissions
    # ----------------------------------------------
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    # ----------------------------------------------
    # Filtering
    # ----------------------------------------------
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",),
    # ----------------------------------------------
    # OpenAPI Schema
    # ----------------------------------------------
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}


# ==================================================
# Simple JWT
# ==================================================

SIMPLE_JWT = {
    # ----------------------------------------------
    # Token lifetime
    # ----------------------------------------------
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    # ----------------------------------------------
    # Refresh token rotation
    # ----------------------------------------------
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    # ----------------------------------------------
    # Authorization header
    # ----------------------------------------------
    "AUTH_HEADER_TYPES": ("Bearer",),
}


# ==================================================
# DRF Spectacular / Swagger
# ==================================================

SPECTACULAR_SETTINGS = {
    "TITLE": "FarmHub API",
    "DESCRIPTION": (
        "REST API for FarmHub farm, farmer, "
        "cattle, milk production, and activity management."
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SWAGGER_UI_SETTINGS": {
        "persistAuthorization": True,
    },
}
