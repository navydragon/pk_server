"""Агрегация KPI и серий для страницы базовой аналитики."""

from datetime import datetime, time, timedelta
from django.contrib.auth import get_user_model
from django.db.models import Avg, Count, DurationField, ExpressionWrapper, F
from django.db.models.functions import TruncDate
from django.utils import timezone
from django.utils.dateparse import parse_date

from core.choices import (
    ApplicationStatus,
    CallbackRequestStatus,
    CorporateRequestStatus,
    CourseBatchStatus,
    ProgramStatus,
)
from core.models import (
    Application,
    CallbackRequest,
    CorporateRequest,
    CourseBatch,
    Direction,
    Program,
)
from publications.choices import PublicationStatus
from publications.models import Case, Publication, Testimonial

User = get_user_model()

PRESET_DAYS = {7, 30, 90}
DEFAULT_PRESET = 30


def _aware(dt):
    if timezone.is_naive(dt):
        return timezone.make_aware(dt, timezone.get_current_timezone())
    return dt


def _parse_bound(value, end_of_day=False):
    if not value:
        return None
    parsed = parse_date(value)
    if not parsed:
        return None
    clock = time.max if end_of_day else time.min
    return _aware(datetime.combine(parsed, clock))


def resolve_period(params):
    """
    Возвращает (date_from, date_to, previous_from, previous_to, preset, filters_dict).

    По умолчанию — последние 30 дней включительно до сейчас.
    """
    now = timezone.now()
    preset_raw = params.get('preset') or ''
    date_from = _parse_bound(params.get('date_from'))
    date_to = _parse_bound(params.get('date_to'), end_of_day=True)

    preset = None
    if date_from and date_to and date_from <= date_to:
        pass
    else:
        try:
            preset = int(preset_raw) if preset_raw else DEFAULT_PRESET
        except (TypeError, ValueError):
            preset = DEFAULT_PRESET
        if preset not in PRESET_DAYS:
            preset = DEFAULT_PRESET
        date_to = now
        date_from = _aware(
            datetime.combine((now - timedelta(days=preset - 1)).date(), time.min)
        )

    duration = date_to - date_from
    previous_to = date_from - timedelta(microseconds=1)
    previous_from = previous_to - duration

    filters = {
        'preset': str(preset) if preset else '',
        'date_from': date_from.date().isoformat(),
        'date_to': date_to.date().isoformat(),
        'direction': params.get('direction') or '',
        'assigned_to': params.get('assigned_to') or '',
    }
    return date_from, date_to, previous_from, previous_to, preset, filters


def _delta_pct(current, previous):
    if previous == 0:
        if current == 0:
            return 0
        return 100
    return round((current - previous) / previous * 100, 1)


def _apply_crm_scope(qs, *, direction_id=None, assigned_to=None, program_field='program'):
    if direction_id:
        try:
            qs = qs.filter(**{f'{program_field}__direction_id': int(direction_id)})
        except (TypeError, ValueError):
            pass
    if assigned_to == 'none':
        qs = qs.filter(assigned_to__isnull=True)
    elif assigned_to:
        try:
            qs = qs.filter(assigned_to_id=int(assigned_to))
        except (TypeError, ValueError):
            pass
    return qs


def _daily_counts(queryset, date_from, date_to):
    """Словарь date -> count по TruncDate."""
    rows = (
        queryset.filter(created_at__gte=date_from, created_at__lte=date_to)
        .annotate(day=TruncDate('created_at'))
        .values('day')
        .annotate(c=Count('id'))
        .order_by('day')
    )
    return {row['day']: row['c'] for row in rows if row['day']}


def _fill_daily_series(date_from, date_to, counts_map):
    labels = []
    values = []
    day = date_from.date()
    end = date_to.date()
    while day <= end:
        labels.append(day.strftime('%d.%m'))
        values.append(counts_map.get(day, 0))
        day += timedelta(days=1)
    return labels, values


def _status_breakdown(queryset, choices, date_from, date_to):
    counts = {
        row['status']: row['c']
        for row in (
            queryset.filter(created_at__gte=date_from, created_at__lte=date_to)
            .values('status')
            .annotate(c=Count('id'))
        )
    }
    labels = []
    values = []
    for code, label in choices:
        labels.append(label)
        values.append(counts.get(code, 0))
    return labels, values


def build_analytics(params, *, include_crm=True, include_catalog=True, include_content=True):
    """Собирает полный контекст аналитики для шаблона."""
    date_from, date_to, prev_from, prev_to, preset, filters = resolve_period(params)
    direction_id = filters['direction'] or None
    assigned_to = filters['assigned_to'] or None

    context = {
        'filters': filters,
        'preset': preset,
        'date_from': date_from,
        'date_to': date_to,
        'directions': Direction.objects.order_by('name'),
        'assignees': User.objects.filter(is_active=True).order_by('username'),
        'include_crm': include_crm,
        'include_catalog': include_catalog,
        'include_content': include_content,
        'chart_json': {},
    }

    if include_crm:
        context.update(_build_crm_block(
            date_from, date_to, prev_from, prev_to,
            direction_id=direction_id,
            assigned_to=assigned_to,
        ))
        context['chart_json'].update(context.pop('crm_charts'))

    if include_catalog:
        context.update(_build_catalog_block(
            date_from, date_to,
            direction_id=direction_id,
        ))
        context['chart_json'].update(context.pop('catalog_charts'))

    if include_content:
        context.update(_build_content_block(date_from, date_to))
        context['chart_json'].update(context.pop('content_charts'))

    return context


def _build_crm_block(date_from, date_to, prev_from, prev_to, *, direction_id, assigned_to):
    apps = _apply_crm_scope(
        Application.objects.all(),
        direction_id=direction_id,
        assigned_to=assigned_to,
    )
    # Corporate and callback don't have program/direction FK the same way
    corps = CorporateRequest.objects.all()
    if assigned_to == 'none':
        corps = corps.filter(assigned_to__isnull=True)
    elif assigned_to:
        try:
            corps = corps.filter(assigned_to_id=int(assigned_to))
        except (TypeError, ValueError):
            pass
    if direction_id:
        try:
            corps = corps.filter(directions__id=int(direction_id)).distinct()
        except (TypeError, ValueError):
            pass

    calls = CallbackRequest.objects.all()
    if assigned_to == 'none':
        calls = calls.filter(assigned_to__isnull=True)
    elif assigned_to:
        try:
            calls = calls.filter(assigned_to_id=int(assigned_to))
        except (TypeError, ValueError):
            pass

    apps_cur = apps.filter(created_at__gte=date_from, created_at__lte=date_to)
    corps_cur = corps.filter(created_at__gte=date_from, created_at__lte=date_to)
    calls_cur = calls.filter(created_at__gte=date_from, created_at__lte=date_to)

    apps_prev = apps.filter(created_at__gte=prev_from, created_at__lte=prev_to).count()
    corps_prev = corps.filter(created_at__gte=prev_from, created_at__lte=prev_to).count()
    calls_prev = calls.filter(created_at__gte=prev_from, created_at__lte=prev_to).count()

    apps_count = apps_cur.count()
    corps_count = corps_cur.count()
    calls_count = calls_cur.count()
    incoming = apps_count + corps_count + calls_count
    incoming_prev = apps_prev + corps_prev + calls_prev

    backlog_new = (
        apps.filter(status=ApplicationStatus.NEW).count()
        + corps.filter(status=CorporateRequestStatus.NEW).count()
        + calls.filter(status=CallbackRequestStatus.NEW).count()
    )

    converted = apps_cur.filter(
        status__in=[ApplicationStatus.CONFIRMED, ApplicationStatus.COMPLETED]
    ).count()
    conversion_pct = round(converted / apps_count * 100, 1) if apps_count else 0

    quote_done = corps_cur.filter(
        status__in=[CorporateRequestStatus.QUOTE_SENT, CorporateRequestStatus.CLOSED]
    ).count()
    quote_pct = round(quote_done / corps_count * 100, 1) if corps_count else 0

    closed_qs = apps_cur.filter(
        status__in=[ApplicationStatus.COMPLETED, ApplicationStatus.REJECTED]
    ).annotate(
        duration=ExpressionWrapper(
            F('updated_at') - F('created_at'),
            output_field=DurationField(),
        )
    )
    avg_duration = closed_qs.aggregate(avg=Avg('duration'))['avg']
    if avg_duration is not None:
        avg_close_hours = round(avg_duration.total_seconds() / 3600, 1)
    else:
        avg_close_hours = None

    # Daily series
    labels, app_vals = _fill_daily_series(
        date_from, date_to, _daily_counts(apps, date_from, date_to)
    )
    _, corp_vals = _fill_daily_series(
        date_from, date_to, _daily_counts(corps, date_from, date_to)
    )
    _, call_vals = _fill_daily_series(
        date_from, date_to, _daily_counts(calls, date_from, date_to)
    )

    app_status_labels, app_status_values = _status_breakdown(
        apps, ApplicationStatus.CHOICES, date_from, date_to
    )
    corp_status_labels, corp_status_values = _status_breakdown(
        corps, CorporateRequestStatus.CHOICES, date_from, date_to
    )

    top_programs = list(
        apps_cur.values('program_id', 'program__name')
        .annotate(c=Count('id'))
        .order_by('-c')[:8]
    )
    top_program_labels = [r['program__name'] or f"#{r['program_id']}" for r in top_programs]
    top_program_values = [r['c'] for r in top_programs]

    directions_table = list(
        apps_cur.values('program__direction_id', 'program__direction__name')
        .annotate(c=Count('id'))
        .order_by('-c')
    )

    return {
        'crm_kpi': {
            'incoming': incoming,
            'incoming_delta': _delta_pct(incoming, incoming_prev),
            'apps_count': apps_count,
            'corps_count': corps_count,
            'calls_count': calls_count,
            'backlog_new': backlog_new,
            'conversion_pct': conversion_pct,
            'quote_pct': quote_pct,
            'avg_close_hours': avg_close_hours,
        },
        'directions_table': directions_table,
        'crm_charts': {
            'incoming_daily': {
                'labels': labels,
                'applications': app_vals,
                'corporate': corp_vals,
                'callbacks': call_vals,
            },
            'application_statuses': {
                'labels': app_status_labels,
                'values': app_status_values,
            },
            'top_programs': {
                'labels': top_program_labels,
                'values': top_program_values,
            },
            'corporate_statuses': {
                'labels': corp_status_labels,
                'values': corp_status_values,
            },
        },
    }


def _build_catalog_block(date_from, date_to, *, direction_id):
    programs = Program.objects.all()
    batches = CourseBatch.objects.all()
    if direction_id:
        try:
            did = int(direction_id)
            programs = programs.filter(direction_id=did)
            batches = batches.filter(program__direction_id=did)
        except (TypeError, ValueError):
            pass

    active = programs.filter(status=ProgramStatus.ACTIVE).count()
    draft = programs.filter(status=ProgramStatus.DRAFT).count()
    archived = programs.filter(status=ProgramStatus.ARCHIVED).count()
    open_batches = batches.filter(status=CourseBatchStatus.ENROLLMENT_OPEN).count()
    new_programs = programs.filter(
        created_at__gte=date_from, created_at__lte=date_to
    ).count()

    apps = Application.objects.filter(
        created_at__gte=date_from, created_at__lte=date_to
    )
    if direction_id:
        try:
            apps = apps.filter(program__direction_id=int(direction_id))
        except (TypeError, ValueError):
            pass
    top = (
        apps.values('program__name')
        .annotate(c=Count('id'))
        .order_by('-c')
        .first()
    )

    status_counts = {
        row['status']: row['c']
        for row in programs.values('status').annotate(c=Count('id'))
    }
    prog_labels = [label for _, label in ProgramStatus.CHOICES]
    prog_values = [status_counts.get(code, 0) for code, _ in ProgramStatus.CHOICES]

    return {
        'catalog_kpi': {
            'active_programs': active,
            'draft_programs': draft,
            'archived_programs': archived,
            'open_batches': open_batches,
            'new_programs': new_programs,
            'top_program_name': top['program__name'] if top else '—',
            'top_program_apps': top['c'] if top else 0,
        },
        'catalog_charts': {
            'program_statuses': {
                'labels': prog_labels,
                'values': prog_values,
            },
        },
    }


def _build_content_block(date_from, date_to):
    pub_published = Publication.objects.filter(status=PublicationStatus.PUBLISHED).count()
    case_published = Case.objects.filter(status=PublicationStatus.PUBLISHED).count()
    test_published = Testimonial.objects.filter(status=PublicationStatus.PUBLISHED).count()

    queue = (
        Publication.objects.filter(
            status__in=[PublicationStatus.DRAFT, PublicationStatus.ON_MODERATION]
        ).count()
        + Case.objects.filter(
            status__in=[PublicationStatus.DRAFT, PublicationStatus.ON_MODERATION]
        ).count()
        + Testimonial.objects.filter(
            status__in=[PublicationStatus.DRAFT, PublicationStatus.ON_MODERATION]
        ).count()
    )

    pubs_period = Publication.objects.filter(
        created_at__gte=date_from, created_at__lte=date_to
    ).count()
    cases_period = Case.objects.filter(
        created_at__gte=date_from, created_at__lte=date_to
    ).count()
    tests_period = Testimonial.objects.filter(
        created_at__gte=date_from, created_at__lte=date_to
    ).count()

    # published vs draft by type (snapshot)
    def _pair(model):
        return (
            model.objects.filter(status=PublicationStatus.PUBLISHED).count(),
            model.objects.filter(status=PublicationStatus.DRAFT).count(),
        )

    pub_p, pub_d = _pair(Publication)
    case_p, case_d = _pair(Case)
    test_p, test_d = _pair(Testimonial)

    return {
        'content_kpi': {
            'publications_published': pub_published,
            'cases_published': case_published,
            'testimonials_published': test_published,
            'published_total': pub_published + case_published + test_published,
            'editor_queue': queue,
            'created_in_period': pubs_period + cases_period + tests_period,
        },
        'content_charts': {
            'content_by_type': {
                'labels': ['Новости', 'Кейсы', 'Отзывы'],
                'published': [pub_p, case_p, test_p],
                'draft': [pub_d, case_d, test_d],
            },
        },
    }
