"""Общие хелперы для queryset'ов."""

from __future__ import annotations

from django.db.models import QuerySet

from core.settings_service import is_show_test_data_enabled


def exclude_test_data(qs: QuerySet, field: str = 'is_test') -> QuerySet:
    """Скрывает тестовые записи, если настройка show_test_data выключена."""
    if is_show_test_data_enabled():
        return qs
    return qs.filter(**{field: False})
