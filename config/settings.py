import os
import sys
from datetime import timedelta
from pathlib import Path


try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    load_dotenv = None
    
    
BASE_DIR = Path(__file__).resolve().parent.parent

_APPS_DIR = BASE_DIR / 'apps'
if str(_APPS_DIR) not in sys.path:
    sys.path.insert(0, str(_APPS_DIR))


SECRET_KEY = 'django-insecure-_be8&r60022kn5csg0q*p-=p=ij1$nr4ol0=rtkl+v_6btb3ka'

DEBUG = True

ALLOWED_HOSTS = ["*"]


LOCAL_APPS = [
    'content',
    'commerce',
    'leads',
]

INSTALLED_APPS = [
    'daphne',
    'channels',
    'jazzmin',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'drf_spectacular',
    'corsheaders',
    'django_filters',
    *LOCAL_APPS,
]

_COMPANY_ADMIN_LABEL = 'ООО «МАКСАН ГРУПП»'

JAZZMIN_SETTINGS = {
    "site_title": _COMPANY_ADMIN_LABEL,
    "site_header": _COMPANY_ADMIN_LABEL,
    "site_brand": _COMPANY_ADMIN_LABEL,
    "welcome_sign": f'Панель управления {_COMPANY_ADMIN_LABEL}',
    "copyright": _COMPANY_ADMIN_LABEL,
    "topmenu_links": [
        {"name": "Swagger", "url": "/docs/", "new_window": True},
        {"name": "ReDoc", "url": "/redoc/", "new_window": True},
    ],
    "show_sidebar": True,
    "navigation_expanded": True,
    "order_with_respect_to": [
        "content",
        "commerce",
        "leads",
    ],
    "icons": {
        "content.Banner": "fas fa-image",
        "content.Certification": "fas fa-certificate",
        "content.AboutCompany": "fas fa-building",
        "content.News": "fas fa-newspaper",
        "content.NewsImage": "fas fa-photo-video",
        "commerce.Manufacturer": "fas fa-industry",
        "commerce.Product": "fas fa-tools",
        "commerce.ProductImage": "fas fa-camera",
        "commerce.Order": "fas fa-shopping-cart",
        "commerce.OrderProduct": "fas fa-stream",
        "leads.FeedbackMessage": "fas fa-envelope-open-text",
        "leads.Contact": "fas fa-map-marked-alt",
        "leads.ContactPhone": "fas fa-phone-alt",
    },
    "default_icon_parents": "fas fa-folder",
    "default_icon_children": "fas fa-circle",
    "custom_css": "admin/css/custom_admin.css",
}

LOCAL_MIDDLEWARE = [
    'config.middleware.middleware.JsonErrorResponseMiddleware',
    'config.middleware.middleware.Custom404Middleware',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'config.middleware.apikey_middleware.BackendApiKeyMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    *LOCAL_MIDDLEWARE,
]

ROOT_URLCONF = 'config.urls'

# ASGI: Daphne / Hypercorn / Uvicorn. В INSTALLED_APPS `daphne` стоит до staticfiles —
# тогда `manage.py runserver` тоже поднимает Daphne.
# Явный запуск: `daphne -b 0.0.0.0 -p 8000 config.asgi:application` или `scripts/run-daphne.ps1`
ASGI_APPLICATION = 'config.asgi.application'

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    }
}

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'config.admin_alerts_context.admin_global_alerts',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

# Database — PostgreSQL by default; USE_SQLITE=1 for local dev / CI without Postgres
USE_SQLITE = os.getenv('USE_SQLITE', '').strip().lower() in ('1', 'true', 'yes')
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
        'CONN_MAX_AGE': 600,
        'OPTIONS': {
            'client_encoding': 'UTF8',
        },
    }
}
    


AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'ru'

TIME_ZONE = 'Europe/Moscow'

USE_I18N = True

USE_TZ = True


STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

MEDIA_URL = "/media/"
MEDIA_ROOT = os.getenv('MEDIA_ROOT', str(BASE_DIR / '/var/www/media'))


LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale'),
]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],
    'DEFAULT_AUTHENTICATION_CLASSES': [],
    "DEFAULT_PARSER_CLASSES": (
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.FormParser",
        "rest_framework.parsers.MultiPartParser",
        "rest_framework.parsers.FileUploadParser",
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    "PAGE_SIZE": 24,
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=7),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
}

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:5173",
    "https://adent-admin.migfastkg.ru"
]

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:5173",
    "https://sudo certbot --nginx -d"
]

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
CORS_EXPOSE_HEADERS = ['Content-Type', 'X-CSRFToken']

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'cache-control',
    'pragma',
]

CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

CSRF_COOKIE_SECURE = False
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_USE_SESSIONS = False
CSRF_COOKIE_NAME = 'csrftoken'

SESSION_COOKIE_SECURE = False
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_HTTPONLY = True

SECURE_CROSS_ORIGIN_OPENER_POLICY = None

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
)

SITE_ID = 1


EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'true').strip().lower() in ('1', 'true', 'yes', 'y')
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '').strip()
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '').strip()

EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', '').strip() or (
    'django.core.mail.backends.smtp.EmailBackend'
    if (EMAIL_HOST_USER and EMAIL_HOST_PASSWORD)
    else 'django.core.mail.backends.console.EmailBackend'
)

DEFAULT_FROM_EMAIL = (
    os.getenv('DEFAULT_FROM_EMAIL', '').strip()
    or EMAIL_HOST_USER
    or 'no-reply@ecommerce-mg.local'
)

SPECTACULAR_SETTINGS = {
    'TITLE': 'Ecommerce MG API',
    'DESCRIPTION': (
        'Публичный REST API интернет‑витрины (баннеры, контент, каталог запчастей и шин, '
        'новости, контакты, заказы без регистрации).'
    ),
    'VERSION': '1.0.0',
    'COMPONENT_SPLIT_REQUEST': True,
    'TAGS': [
        {'name': 'Главная — баннеры', 'description': 'Слайдер главной страницы (только чтение).'},
        {'name': 'Сертификаты', 'description': 'Сертификаты компании: превью и PDF (только чтение).'},
        {'name': 'Компания', 'description': 'Страница «О компании» с метриками.'},
        {'name': 'Новости', 'description': 'Лента материалов с фильтром по типу и пагинацией.'},
        {'name': 'Обращения', 'description': 'Форма обратной связи (POST).'},
        {'name': 'Контакты', 'description': 'Адрес, email и каналы связи по телефонам.'},
        {'name': 'Производители', 'description': 'Список партнёрских брендов и детальные карточки.'},
        {
            'name': 'Каталог — товары',
            'description': (
                'Каталог запчастей и шин: фильтрация по типу, производителю, цене, '
                'сортировка по цене (order_price=asc|desc), поиск по названию.'
            ),
        },
         {'name': 'Заказы', 'description': 'Приём заказов с корзины (гостевая отправка через POST).'},
    ],
    'PREPROCESSING_HOOKS': [],
    'POSTPROCESSING_HOOKS': [],
    'GENERIC_ADDITIONAL_PROPERTIES': None,
    'CAMPAIGN': None,
    'CONTACT': {
        'name': 'Поддержка API Ecommerce MG',
        'email': 'support@ecommerce-mg.ru',
    },
    'LICENSE': {
        'name': 'Проприетарная лицензия',
    },
}

PASSWORD_RESET_CODE_TTL_MINUTES = int(os.getenv('PASSWORD_RESET_CODE_TTL_MINUTES', '15'))
PASSWORD_RESET_SESSION_TTL_MINUTES = int(os.getenv('PASSWORD_RESET_SESSION_TTL_MINUTES', '15'))

BACKEND_API_KEY = os.getenv('BACKEND_API_KEY', '').strip()
REQUIRE_BACKEND_API_KEY = os.getenv('REQUIRE_BACKEND_API_KEY', 'false').strip().lower() in ('1', 'true', 'yes')

