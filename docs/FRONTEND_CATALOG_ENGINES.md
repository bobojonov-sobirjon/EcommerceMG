# Каталог и страницы двигателей — документация для фронтенда

Документ описывает API каталога товаров с учётом новой категории **«Двигатели»** и страниц производителей с баннером (макеты Figma: Cummins, Caterpillar, Deutz, Weichai, Komatsu, MTU, Perkins, Volvo Penta).

**Базовый URL API:** `/api/v1/`  
**Swagger UI:** `/docs/`  
**OpenAPI schema:** `/schema/`

Все эндпоинты каталога — **GET**, авторизация не требуется.

---

## 1. Логика каталога (важно)

В каталоге **три раздела**. Поведение разное:

| Раздел | `type` | Поведение на фронте | Баннер сверху |
|--------|--------|---------------------|---------------|
| Запчасти | `spare_parts` | Сразу список товаров | **Нет** |
| Шины | `tires` | Сразу список товаров | **Нет** |
| Двигатели | `engines` | Сначала список **производителей**, затем страница производителя | **Да** (привязан к производителю) |

### Баннеры не переключаются автоматически

Это **не карусель** и не слайдер каталога. На странице производителя двигателей всегда показывается **один** баннер этого производителя + его товары.

### Не путать с баннерами главной

| Источник | Эндпоинт | Назначение |
|----------|----------|------------|
| `GET /api/v1/banners/` | Контент сайта | Слайдер **на главной** странице |
| `GET /api/v1/engines/manufacturers/slug/{slug}/` | Каталог | Баннер **страницы двигателей** производителя |

---

## 2. Навигация (рекомендуемые маршруты)

```
/catalog
  ├── /spare-parts          → GET /products/?type=spare_parts
  ├── /tires                → GET /products/?type=tires
  └── /engines
        ├── (список)        → GET /engines/manufacturers/
        └── /:slug          → GET /engines/manufacturers/slug/:slug/
              └── /product/:productSlug → GET /products/slug/:productSlug/
```

Список категорий можно взять из API или захардкодить после первого запроса.

---

## 3. Эндпоинты

### 3.1. Категории каталога

```
GET /api/v1/catalog/categories/
```

**Ответ:**

```json
[
  {
    "type": "spare_parts",
    "label": "Запчасти",
    "hub": "products"
  },
  {
    "type": "tires",
    "label": "Шины для спецтехники",
    "hub": "products"
  },
  {
    "type": "engines",
    "label": "Двигатели",
    "hub": "manufacturers"
  }
]
```

**Поле `hub`:**
- `products` — открывать сразу список товаров (`/products/?type=...`)
- `manufacturers` — открывать список производителей (`/engines/manufacturers/`)

---

### 3.2. Запчасти и шины (без изменений)

```
GET /api/v1/products/?type=spare_parts
GET /api/v1/products/?type=tires
```

**Query-параметры:**

| Параметр | Тип | Описание |
|----------|-----|----------|
| `type` | string | `spare_parts` \| `tires` \| `engines` |
| `manufacturer` | int | ID производителя |
| `search` / `name` | string | Поиск по названию, артикулу, описанию |
| `min_price` | decimal | Мин. цена |
| `max_price` | decimal | Макс. цена |
| `order_price` | string | `asc` — дешевле, `desc` — дороже |
| `page` | int | Страница (по умолчанию `1`) |
| `page_size` | int | Размер страницы (по умолчанию `20`, макс. `100`) |

**Формат ответа (пагинация):**

```json
{
  "count": 42,
  "page": 1,
  "page_size": 20,
  "total_pages": 3,
  "results": [ /* ProductList[] */ ]
}
```

**Карточка товара в списке (`ProductList`):**

```json
{
  "id": 1,
  "product_type": "spare_parts",
  "product_type_label": "Запчасти",
  "name": "ФИЛЬТР МАСЛЯНЫЙ CAT",
  "slug": "filtr-maslyanyy-cat-1r-0716",
  "artikul": "1R-0716",
  "price": "4250.50",
  "is_stock": true,
  "manufacturer": {
    "id": 1,
    "name": "Caterpillar"
  },
  "thumbnail": "https://example.com/media/products/2026/06/prod_1_0.jpg"
}
```

---

### 3.3. Двигатели — список производителей

Показываются **только** производители, у которых есть хотя бы один товар с `product_type = engines`.

```
GET /api/v1/engines/manufacturers/
```

**Ответ:** массив `ManufacturerList[]`

```json
[
  {
    "id": 2,
    "name": "Cummins",
    "slug": "cummins",
    "logo": "/media/manufacturers/logos/2026/06/logo_cummins.jpg",
    "ordering": 10
  }
]
```

> **Медиа:** в этом эндпоинте `logo` может приходить как относительный путь `/media/...`. Добавляйте origin сайта при необходимости.

---

### 3.4. Двигатели — страница производителя (основной экран Figma)

**Рекомендуется использовать slug** (ЧПУ в URL).

```
GET /api/v1/engines/manufacturers/slug/{slug}/
GET /api/v1/engines/manufacturers/{id}/          # альтернатива по id
```

**Query-параметры (только для списка товаров внизу):**

| Параметр | Описание |
|----------|----------|
| `page` | Страница товаров (default: `1`) |
| `page_size` | Размер страницы (default: `20`, max: `100`) |
| `order_price` | `asc` \| `desc` |
| `search` / `name` | Поиск по двигателям этого производителя |
| `min_price` / `max_price` | Фильтр по цене |

**Пример:** `GET /api/v1/engines/manufacturers/slug/cummins/?page=1&page_size=12`

**Ответ:**

```json
{
  "manufacturer": {
    "id": 2,
    "name": "Cummins",
    "slug": "cummins",
    "description": "Надёжные дизельные двигатели для спецтехники...",
    "seo_title": "Двигатели Cummins — купить",
    "seo_description": "...",
    "logo": "https://example.com/media/manufacturers/logos/.../logo.jpg",
    "hero_image": "https://example.com/media/manufacturers/hero/.../banner.jpg",
    "features_heading": "",
    "features": [],
    "ordering": 10
  },
  "products": {
    "count": 3,
    "page": 1,
    "page_size": 20,
    "total_pages": 1,
    "results": [
      {
        "id": 15,
        "product_type": "engines",
        "product_type_label": "Двигатели",
        "name": "Двигатель Cummins ISF 2.8",
        "slug": "dvigatel-cummins-isf-2-8-eng-cum-isf28",
        "artikul": "ENG-CUM-ISF28",
        "price": "485000.00",
        "is_stock": true,
        "manufacturer": { "id": 2, "name": "Cummins" },
        "thumbnail": "https://example.com/media/products/.../engine_15_0.jpg"
      }
    ]
  }
}
```

#### Вёрстка страницы по блокам

```
┌─────────────────────────────────────────┐
│  hero_image          ← баннер (фон/картинка) │
│  name / seo_title    ← заголовок H1          │
│  description         ← текст под баннером    │
├─────────────────────────────────────────┤
│  features_heading    ← опционально (H2)      │
│  features[]          ← 0–3+ карточки         │
│    · title                                   │
│    · description                             │
│    · icon (nullable, absolute URL)           │
├─────────────────────────────────────────┤
│  products.results    ← сетка карточек        │
│  пагинация           ← products.page, count  │
└─────────────────────────────────────────┘
```

**Пример с блоком преимуществ (Caterpillar):**

```json
{
  "features_heading": "Особенности двигателей Caterpillar",
  "features": [
    {
      "id": 1,
      "title": "НАДЁЖНОСТЬ",
      "description": "Двигатели CAT рассчитаны на экстремальные нагрузки...",
      "icon": null,
      "ordering": 0
    },
    {
      "id": 2,
      "title": "ЭФФЕКТИВНОСТЬ",
      "description": "...",
      "icon": null,
      "ordering": 1
    }
  ]
}
```

Если `features` пустой — блок не показывать. У Cummins в макете может быть только баннер + текст без карточек.

---

### 3.5. Карточка товара (все категории)

```
GET /api/v1/products/slug/{slug}/
GET /api/v1/products/{id}/
```

**Ответ (`ProductDetail`):**

```json
{
  "id": 15,
  "product_type": "engines",
  "product_type_label": "Двигатели",
  "manufacturer": { "id": 2, "name": "Cummins" },
  "name": "Двигатель Cummins ISF 2.8",
  "slug": "dvigatel-cummins-isf-2-8-eng-cum-isf28",
  "artikul": "ENG-CUM-ISF28",
  "description": "",
  "seo_title": "...",
  "seo_description": "...",
  "price": "485000.00",
  "price_on_request": false,
  "is_stock": true,
  "images": [
    { "id": 1, "image": "/media/products/2026/06/engine_15_0.jpg", "ordering": 0 }
  ]
}
```

**Похожие товары:**

```
GET /api/v1/products/slug/{slug}/similar/
```

Возвращает до 24 товаров того же производителя и **того же `product_type`**.

---

### 3.6. Производители (блок «С кем работаем»)

Отдельно от каталога двигателей — для главной и страницы «О нас»:

```
GET /api/v1/manufacturers/
GET /api/v1/manufacturers/slug/{slug}/
```

`ManufacturerDetail` содержит `hero_image`, `features_heading`, но **без** вложенного `features[]` и **без** списка товаров. Для страницы двигателей используйте только `/engines/manufacturers/...`.

---

## 4. SEO-поля

Поля `slug`, `seo_title`, `seo_description` хранятся в отдельной SEO-модели на бэкенде, в API отдаются как обычные поля объекта.

| Сущность | SEO в списке | SEO в деталке |
|----------|--------------|---------------|
| Товар | `slug` | `slug`, `seo_title`, `seo_description` |
| Производитель (двигатели) | `slug` | все три + баннер |
| Новость | `slug` | все три |

Для `<title>` и meta description страницы двигателей:

```html
<title>{manufacturer.seo_title || manufacturer.name}</title>
<meta name="description" content="{manufacturer.seo_description}" />
```

---

## 5. Типы товаров (enum)

| Значение API | Отображаемое название |
|--------------|---------------------|
| `spare_parts` | Запчасти |
| `tires` | Шины для спецтехники |
| `engines` | Двигатели |

---

## 6. Медиа-файлы

- Префикс: `/media/...`
- На странице двигателей (`/engines/manufacturers/slug/...`) поля `hero_image`, `logo`, `features[].icon` приходят как **полные URL** (с доменом).
- В других эндпоинтах часть полей может быть относительной — проверяйте: если путь начинается с `/media/`, склеивайте с `window.location.origin` или базовым URL API.

---

## 7. Обработка ошибок

| Код | Когда |
|-----|-------|
| `404` | Неизвестный `slug` производителя или товара |
| `200` + пустой `engines/manufacturers/` | Ещё нет производителей с товарами типа «Двигатели» |

---

## 8. Чеклист для фронтенда

- [ ] Экран каталога: 3 категории из `/catalog/categories/`
- [ ] Запчасти / шины: список без баннера, `GET /products/?type=...`
- [ ] Двигатели: список производителей `GET /engines/manufacturers/`
- [ ] Страница Cummins/CAT/Deutz: один запрос `GET /engines/manufacturers/slug/{slug}/`
- [ ] Баннер = `manufacturer.hero_image`, текст = `description`
- [ ] Блок преимуществ: `features_heading` + `features[]` (если не пусто)
- [ ] Сетка товаров = `products.results`, пагинация по `products.page` / `total_pages`
- [ ] Карточка товара: `GET /products/slug/{slug}/`
- [ ] Не использовать `/banners/` для страниц двигателей

---

## 9. Связанные эндпоинты (контекст)

| Эндпоинт | Назначение |
|----------|------------|
| `GET /api/v1/banners/` | Слайдер главной |
| `GET /api/v1/about/` | О компании |
| `GET /api/v1/news/` | Новости |
| `GET /api/v1/contacts/` | Контакты |
| `POST /api/v1/orders/` | Оформление заказа |
| `POST /api/v1/messages/` | Форма обратной связи |

---

## 10. Цена по запросу

У товара есть поле `price_on_request` (boolean).

| `price_on_request` | `price` в API | Что показывать на фронте |
|--------------------|---------------|--------------------------|
| `true` | `null` | **«Цена по запросу»** |
| `false` | число, напр. `"99999.00"` | Обычная цена |

**Обязательная логика на фронте (все категории: запчасти, шины, двигатели):**

```js
if (product.price_on_request) {
  // показать «Цена по запросу»
} else {
  // показать product.price
}
```

Нельзя опираться только на `price`: при «цене по запросу» бэкенд отдаёт `price: null`, чтобы случайно не показать старую сумму (например 99999).

Такие товары **нельзя** оформить через `POST /orders/` — API вернёт ошибку. Используйте форму обратной связи.

---

*Документ актуален для ветки с миграцией `commerce.0008_product_price_on_request`. При изменениях API смотрите `/docs/` (Swagger).*
