from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env(name: str, default: str | None = None) -> str | None:
    return os.getenv(name, default)


SECRET_KEY = env("APP_SECRET_KEY", "dev-only-insecure-key")
DEBUG = env("APP_DEBUG", "true").lower() == "true"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = env("USE_X_FORWARDED_HOST", "true").lower() == "true"
SECURE_SSL_REDIRECT = env("SECURE_SSL_REDIRECT", "false").lower() == "true"
SESSION_COOKIE_SECURE = env("SESSION_COOKIE_SECURE", "false").lower() == "true"
CSRF_COOKIE_SECURE = env("CSRF_COOKIE_SECURE", "false").lower() == "true"

ALLOWED_HOSTS = [
    host.strip()
    for host in env("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in env("CSRF_TRUSTED_ORIGINS", "").split(",")
    if origin.strip()
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "apps.assistant",
    "apps.core",
    "apps.repository",
    "apps.search",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DB_ENGINE = env("DB_ENGINE", "postgres").lower()
if DB_ENGINE == "postgres":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env("POSTGRES_DB", "nbs_readapt"),
            "USER": env("POSTGRES_USER", "nbs_readapt"),
            "PASSWORD": env("POSTGRES_PASSWORD", ""),
            "HOST": env("POSTGRES_HOST", "localhost"),
            "PORT": env("POSTGRES_PORT", "5432"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
}

APP_NAME = env("APP_NAME", "nbs-readapt")
APP_ENV = env("APP_ENV", "development")
APP_PORT = int(env("APP_PORT", "9500"))

OPENSEARCH = {
    "url": env("OPENSEARCH_URL", "http://localhost:9200"),
    "username": env("OPENSEARCH_USERNAME", "admin"),
    "password": env("OPENSEARCH_PASSWORD", ""),
    "index_bm25": env("OPENSEARCH_INDEX_BM25", "nbs_repository_bm25"),
    "index_neural": env("OPENSEARCH_INDEX_NEURAL", "nbs_repository_neural"),
    "ingest_pipeline": env("OPENSEARCH_INGEST_PIPELINE", "nbs_repository_ingest"),
    "hybrid_pipeline": env("OPENSEARCH_HYBRID_PIPELINE", "nbs_repository_hybrid"),
}

VLLM = {
    "base_url": (env("RUNPOD_VLLM_HOST") or "").rstrip("/"),
    "chat_completions_url": env("VLLM_CHAT_COMPLETIONS_URL", "").strip(),
    "api_key": env("VLLM_API_KEY", ""),
    "model": env("VLLM_MODEL", ""),
    "max_model_len": int(env("VLLM_MAX_MODEL_LEN", "65535")),
}

ASSISTANT = {
    "timeout_seconds": int(env("ASSISTANT_TIMEOUT_SECONDS", "120")),
    "max_history_messages": int(env("ASSISTANT_MAX_HISTORY_MESSAGES", "6")),
    "context_records": int(env("ASSISTANT_CONTEXT_RECORDS", "6")),
    "context_field_chars": int(env("ASSISTANT_CONTEXT_FIELD_CHARS", "280")),
    "context_record_chars": int(env("ASSISTANT_CONTEXT_RECORD_CHARS", "1200")),
    "max_query_chars": int(env("ASSISTANT_MAX_QUERY_CHARS", "4000")),
    "approx_chars_per_token": float(env("ASSISTANT_APPROX_CHARS_PER_TOKEN", "3.2")),
    "max_input_tokens": int(env("ASSISTANT_MAX_INPUT_TOKENS", "0")),
    "token_safety_margin": int(env("ASSISTANT_TOKEN_SAFETY_MARGIN", "0")),
    "response_style_default": env("ASSISTANT_RESPONSE_STYLE_DEFAULT", "standard"),
    "relevance_min_score": float(env("ASSISTANT_RELEVANCE_MIN_SCORE", "5.0")),
}

INITIAL_INPUT_DIR = BASE_DIR / env("INITIAL_INPUT_DIR", "initial_input")
DATA_DIR = BASE_DIR / env("DATA_DIR", "data")
