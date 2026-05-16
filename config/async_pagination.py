"""Пагинация для списков (query-string: page, page_size)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, TypeVar

from django.db.models import QuerySet

T = TypeVar('T')


@dataclass
class Page:
    count: int
    page: int
    page_size: int
    total_pages: int
    results: list[Any]


def paginate(
    qs: QuerySet[T],
    *,
    page: int = 1,
    page_size: int = 20,
    max_page_size: int = 100,
) -> Page:
    page = max(1, page)
    page_size = min(max(1, page_size), max_page_size)
    total = qs.count()
    total_pages = max(1, (total + page_size - 1) // page_size)
    if page > total_pages:
        page = total_pages
    offset = (page - 1) * page_size
    window = qs[offset : offset + page_size]
    results = list(window)
    return Page(
        count=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        results=results,
    )


# Совместимость: раньше использовался только async-вариант (DRF APIView async не поддерживает).
AsyncPage = Page


async def async_paginate(
    qs: QuerySet[T],
    *,
    page: int = 1,
    page_size: int = 20,
    max_page_size: int = 100,
) -> Page:
    page = max(1, page)
    page_size = min(max(1, page_size), max_page_size)
    total = await qs.acount()
    total_pages = max(1, (total + page_size - 1) // page_size)
    if page > total_pages:
        page = total_pages
    offset = (page - 1) * page_size
    window = qs[offset : offset + page_size]
    results: list[Any] = []
    async for obj in window:
        results.append(obj)
    return Page(
        count=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        results=results,
    )
