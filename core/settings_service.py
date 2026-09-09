"""Хелперы для чтения и записи настроек (Setting)."""

from __future__ import annotations

from core.models import Setting

SHOW_TEST_DATA = 'show_test_data'

_TRUE_VALUES = frozenset({'true', '1', 'yes', 'on'})


def get_setting(code: str, default: str | None = None) -> str | None:
    try:
        return Setting.objects.get(code=code).value
    except Setting.DoesNotExist:
        return default


def get_bool_setting(code: str, default: bool = False) -> bool:
    value = get_setting(code)
    if value is None:
        return default
    return value.strip().lower() in _TRUE_VALUES


def set_setting(code: str, value: str) -> Setting:
    setting, _ = Setting.objects.update_or_create(
        code=code,
        defaults={'value': value},
    )
    return setting


def is_show_test_data_enabled() -> bool:
    return get_bool_setting(SHOW_TEST_DATA, default=False)
