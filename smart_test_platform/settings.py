"""
Django settings for smart_test_platform project.
"""

import os
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Loads a local .env file if one exists (harmless no-op on Render, where the
# real env vars are set directly in the dashboard instead of a file).
load_dotenv(BASE_DIR / ".env")

# In production (Render, etc.) set real values for these via environment
# variables. Locally, the fallbacks below just work out of the box.
SECRET_KEY = os.environ.get(
    "SECRET_KEY", "django-insecure-dev-only-2@p^8pc-h7nx#v5^&p6opn@&b7vu&hbn0"
)
DEBUG = os.environ.get("DEBUG", "True") == "True"
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "*").split(",")

# Render terminates TLS at the load balancer and forwards plain HTTP, so
# trust its proxy header for request.is_secure() / the CSRF check.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
CSRF_TRUSTED_ORIGINS = [
    f"https://{host}" for host in ALLOWED_HOSTS if host not in ("*", "")
]

INSTALLED_APPS = [
    'jazzmin',                       # must be above django.contrib.admin
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',   # serves static files in production
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'smart_test_platform.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.language',
            ],
        },
    },
]

WSGI_APPLICATION = 'smart_test_platform.wsgi.application'


# Database
# Falls back to a local sqlite file with zero setup; on Render, set
# DATABASE_URL to a Postgres instance's Internal Database URL (the free
# web service's own disk is ephemeral, so sqlite would lose data on deploy).
DATABASES = {
    'default': dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}"
    )
}


AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 6},
    },
]


LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# WhiteNoise serves compressed, cache-busted static files directly from
# gunicorn in production — no separate nginx/CDN needed, and it's free.
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- Auth redirects ---
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'post_login_redirect'
LOGOUT_REDIRECT_URL = 'landing'

# --- OpenRouter ---
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
# Cheap + reliable at returning strict JSON. Swap for any OpenRouter model
# id (e.g. a ":free" one) via the env var without touching code.
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "openai/gpt-4o-mini")

# Optional per-language override, e.g. OPENROUTER_MODEL_KAA=openai/gpt-4o —
# lets you point a low-resource language (Karakalpak has very little
# training data for most models) at a stronger/more expensive model without
# raising the cost of every other language. Falls back to OPENROUTER_MODEL
# when unset for a given language.
OPENROUTER_MODEL_OVERRIDES = {
    "en": os.environ.get("OPENROUTER_MODEL_EN", ""),
    "ru": os.environ.get("OPENROUTER_MODEL_RU", ""),
    "uz": os.environ.get("OPENROUTER_MODEL_UZ", ""),
    "kaa": os.environ.get("OPENROUTER_MODEL_KAA", ""),
}

# How many questions to request from OpenRouter per generation batch. Kept
# small so each HTTP request/response stays well under typical PaaS request
# timeouts even while the whole test (20-100+ questions) builds up.
QUESTION_BATCH_SIZE = 8

# Bump to make every browser drop its offline copies (service worker caches)
# after a deploy that changes cached pages or static files.
PWA_CACHE_VERSION = os.environ.get("PWA_CACHE_VERSION", "teachx-v1")

# ---------------------------------------------------------------------------
# Jazzmin — drop-in skin for the Django admin, which is the "admin can do
# absolutely anything" panel for this platform (full CRUD over every model).
# ---------------------------------------------------------------------------
JAZZMIN_SETTINGS = {
    "site_title": "TeachX Admin",
    "site_header": "TeachX",
    "site_brand": "TEACHX",
    "welcome_sign": "Welcome to the TeachX control room",
    "copyright": "TeachX — Teaching Excellence",
    "search_model": ["auth.User", "core.TestSession"],
    "user_avatar": None,
    "show_sidebar": True,
    "navigation_expanded": True,
    "order_with_respect_to": ["auth", "core"],
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        "core.profile": "fas fa-id-badge",
        "core.subject": "fas fa-book",
        "core.testsession": "fas fa-clipboard-list",
        "core.question": "fas fa-question-circle",
        "core.answer": "fas fa-check-circle",
        "core.teachertest": "fas fa-file-upload",
        "core.teacherquestion": "fas fa-list-ol",
        "core.assignment": "fas fa-user-graduate",
    },
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",
    "related_modal_active": True,
    "use_google_fonts_cdn": True,
    "show_ui_builder": False,
}

JAZZMIN_UI_TWEAKS = {
    "theme": "darkly",
    "default_theme_mode": "dark",
    "navbar": "navbar-dark",
    "no_navbar_border": True,
    "navbar_fixed": True,
    "sidebar": "sidebar-dark-primary",
    "sidebar_fixed": True,
    "accent": "accent-primary",
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success",
    },
}
