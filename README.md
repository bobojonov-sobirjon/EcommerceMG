# Ecommerce MG — серверная часть

**Django** и **REST API** для витрины **ООО «МАКСАН ГРУПП»**: баннеры, контент, каталог (производители, товары), новости, контакты, приём заказов без регистрации. Панель администратора на основе **django-jazzmin**.

## Технологии

- **Python** 3.11 и новее (желательно актуальная ветка 3.12 или 3.13)
- **Django** 5.x, **Django REST Framework**, **drf-spectacular** (описание API), **django-filter**, **django-cors-headers**
- **PostgreSQL** (параметры подключения из переменных окружения)
- **Daphne** и **Channels** (ASGI; маршруты WebSocket при необходимости можно расширить)
- **Simple JWT** (настройки в проекте)
- **Pillow** для работы с изображениями

## Структура каталогов

| Путь | Назначение |
|------|------------|
| `config/` | настройки, маршруты, ASGI и WSGI, промежуточное ПО, файл `api_v1_urls` |
| `apps/content/` | баннеры, страница «О компании», новости |
| `apps/commerce/` | производители, товары, заказы |
| `apps/leads/` | обратная связь, контактные данные сайта |
| `templates/admin/` | переопределение шаблонов админки (общие уведомления о новых заказах) |
| `static/` | статические файлы, в том числе стили админки |

Приложения из каталога `apps/` подключаются через `sys.path` в `manage.py` и в `config/settings.py`.

## Быстрый старт

```bash
python -m venv env
# ОС Windows:
env\Scripts\activate
# Linux или macOS:
# source env/bin/activate

pip install -r requirements.txt
```

Создайте в корне проекта файл **`.env`** (см. таблицу ниже), запустите **PostgreSQL** и выполните:

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

По умолчанию сайт открывается по адресу `http://127.0.0.1:8000/`.

### Запуск через Daphne (ASGI)

```bash
daphne -b 0.0.0.0 -p 8000 config.asgi:application
```

Также можно использовать скрипты `scripts/run-daphne.ps1` и `scripts/run-daphne.sh`.

## Переменные окружения (файл `.env`)

| Имя переменной | Назначение |
|----------------|------------|
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | подключение к **PostgreSQL** (в `config/settings.py` указан этот движок базы данных) |
| `MEDIA_ROOT` | каталог для загружаемых файлов (если не задан — используется папка `media/` в проекте) |
| `BACKEND_API_KEY` | секрет для необязательной проверки запросов |
| `REQUIRE_BACKEND_API_KEY` | значения `true` или `1` включают проверку: в запросе нужен заголовок `X-Backend-Api-Key` |
| `EMAIL_*`, `DEFAULT_FROM_EMAIL`, `EMAIL_BACKEND` | отправка почты (пароли и секреты в репозиторий не помещайте) |

**Важно:** не включайте в систему контроля версий файл `.env` с настоящими паролями. Для рабочего сервера задайте надёжный `SECRET_KEY`, отключите отладку (`DEBUG=False`), ограничьте `ALLOWED_HOSTS` и настройте безопасные параметры cookie и протокола HTTPS в настройках.

## Адреса в браузере

| Путь | Описание |
|------|----------|
| `/admin/` | административная панель (оформление Jazzmin). Если есть непросмотренные заказы (поле `is_seen_moderator=True`), вверху показывается информационная полоса со ссылкой на отфильтрованный список |
| `/api/v1/` | общий префикс открытого программного интерфейса |
| `/docs/` | интерактивная документация **Swagger** |
| `/redoc/` | альтернативная документация **ReDoc** |
| `/schema/` | машиночитаемая схема **OpenAPI** |

### Примеры путей API (префикс `/api/v1/`)

- `banners/`, `about/`, `news/`, `news/<id>/`
- `manufacturers/`, `manufacturers/<id>/`
- `products/`, `products/<id>/`, `products/<id>/similar/`
- `orders/` — метод **POST**: создание заказа
- `messages/` — метод **POST**: форма обратной связи
- `contacts/` — метод **GET**: данные для страницы контактов

## Команды при разработке

```bash
python manage.py check
python manage.py makemigrations
python manage.py migrate
```

Сбор статических файлов перед выкладкой на сервер:

```bash
python manage.py collectstatic --noinput
```

## Лицензия

Внутренний проприетарный проект — условия использования уточняйте у владельца исходного кода.
