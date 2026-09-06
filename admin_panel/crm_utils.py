"""Утилиты фильтрации и CSV-экспорта для CRM-обращений."""

import csv
from datetime import datetime, time
from io import StringIO

from django.http import HttpResponse
from django.utils import timezone
from django.utils.dateparse import parse_date


def _parse_date_bound(value, end_of_day=False):
    if not value:
        return None
    parsed = parse_date(value)
    if not parsed:
        return None
    clock = time.max if end_of_day else time.min
    dt = datetime.combine(parsed, clock)
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.get_current_timezone())
    return dt


def apply_common_crm_filters(queryset, params, *, status_field='status', assigned_field='assigned_to'):
    """Применяет общие фильтры: статус, даты, ответственный."""
    status = params.get('status')
    if status:
        queryset = queryset.filter(**{status_field: status})

    date_from = _parse_date_bound(params.get('date_from'))
    if date_from:
        queryset = queryset.filter(created_at__gte=date_from)

    date_to = _parse_date_bound(params.get('date_to'), end_of_day=True)
    if date_to:
        queryset = queryset.filter(created_at__lte=date_to)

    assigned_to = params.get('assigned_to')
    if assigned_to == 'none':
        queryset = queryset.filter(**{f'{assigned_field}__isnull': True})
    elif assigned_to:
        try:
            queryset = queryset.filter(**{assigned_field: int(assigned_to)})
        except (TypeError, ValueError):
            pass

    return queryset


def csv_response(filename, headers, rows):
    """Формирует HttpResponse с CSV-файлом (UTF-8 BOM для Excel)."""
    buffer = StringIO()
    writer = csv.writer(buffer, delimiter=';')
    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)

    response = HttpResponse(
        '\ufeff' + buffer.getvalue(),
        content_type='text/csv; charset=utf-8',
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
