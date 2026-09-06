from django.db.models import Q

from core.choices import (
    DirectionStatus,
    LearningFormatStatus,
    ProgramStatus,
    ProgramType,
)
from core.models import Direction, LearningFormat, Program

PROGRAM_TYPE_LABELS = {
    ProgramType.QUALIFICATION_UPGRADE: 'Повышение квалификации',
    ProgramType.RETRAINING: 'Профессиональная переподготовка',
}


def _truncate(text: str, limit: int = 280) -> str:
    text = (text or '').strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + '…'


def serialize_program(program: Program) -> dict:
    return {
        'id': program.id,
        'name': program.name,
        'direction': program.direction.name if program.direction_id else '',
        'program_type': program.program_type,
        'program_type_label': PROGRAM_TYPE_LABELS.get(
            program.program_type, program.program_type
        ),
        'learning_format': (
            program.learning_format.name if program.learning_format_id else ''
        ),
        'hours_volume': program.hours_volume,
        'duration': program.duration,
        'cost': program.cost,
        'lead': _truncate(program.lead, 200),
        'target_audience': _truncate(program.target_audience, 200),
        'outcome': _truncate(program.outcome, 160),
        'requirements': _truncate(program.requirements, 160),
    }


def list_directions() -> list[dict]:
    qs = Direction.objects.filter(status=DirectionStatus.ACTIVE).order_by(
        'sort_order', 'name'
    )
    return [{'id': d.id, 'name': d.name} for d in qs]


def list_learning_formats() -> list[dict]:
    qs = LearningFormat.objects.filter(
        status=LearningFormatStatus.ACTIVE
    ).order_by('sort_order', 'name')
    return [{'id': f.id, 'name': f.name} for f in qs]


def get_quiz_filters() -> dict:
    return {
        'directions': list_directions(),
        'formats': list_learning_formats(),
        'program_types': [
            {'id': ProgramType.QUALIFICATION_UPGRADE, 'name': 'Повышение квалификации'},
            {'id': ProgramType.RETRAINING, 'name': 'Профессиональная переподготовка'},
        ],
        'duration_options': [
            {'id': 'short', 'name': 'До 1 месяца', 'max_hours': 48},
            {'id': 'medium', 'name': '1–2 месяца', 'max_hours': 80},
            {'id': 'long', 'name': 'Более 2 месяцев', 'max_hours': None},
            {'id': 'any', 'name': 'Не важно', 'max_hours': None},
        ],
        'budget_options': [
            {'id': '30', 'name': 'До 30 000 ₽', 'max_cost': 30000},
            {'id': '45', 'name': 'До 45 000 ₽', 'max_cost': 45000},
            {'id': '60', 'name': 'До 60 000 ₽', 'max_cost': 60000},
            {'id': 'any', 'name': 'Не важно', 'max_cost': None},
        ],
    }


def search_programs(
    query: str = '',
    direction: str = '',
    program_type: str = '',
    learning_format: str = '',
    max_hours: int | None = None,
    max_cost: int | None = None,
    limit: int = 8,
) -> list[dict]:
    qs = Program.objects.filter(status=ProgramStatus.ACTIVE).select_related(
        'direction', 'learning_format'
    )

    query = (query or '').strip()
    if query:
        qs = qs.filter(
            Q(name__icontains=query)
            | Q(lead__icontains=query)
            | Q(about_description__icontains=query)
            | Q(target_audience__icontains=query)
            | Q(curriculum__icontains=query)
            | Q(direction__name__icontains=query)
        )

    direction = (direction or '').strip()
    if direction:
        qs = qs.filter(direction__name__icontains=direction)

    program_type = (program_type or '').strip().lower()
    if program_type in (ProgramType.QUALIFICATION_UPGRADE, ProgramType.RETRAINING):
        qs = qs.filter(program_type=program_type)
    elif program_type in ('повышение', 'пк'):
        qs = qs.filter(program_type=ProgramType.QUALIFICATION_UPGRADE)
    elif program_type in ('переподготовка', 'пп'):
        qs = qs.filter(program_type=ProgramType.RETRAINING)

    learning_format = (learning_format or '').strip()
    if learning_format:
        qs = qs.filter(learning_format__name__icontains=learning_format)

    if max_hours is not None and max_hours > 0:
        qs = qs.filter(hours_volume__lte=max_hours)

    programs = list(qs.order_by('position', 'name')[: max(limit * 3, 24)])

    if max_cost is not None and max_cost > 0:
        filtered = []
        for program in programs:
            digits = ''.join(ch for ch in str(program.cost) if ch.isdigit())
            if not digits:
                filtered.append(program)
                continue
            if int(digits) <= max_cost:
                filtered.append(program)
        programs = filtered

    return [serialize_program(p) for p in programs[:limit]]


def get_program(program_id: int) -> dict | None:
    try:
        program = Program.objects.select_related(
            'direction', 'learning_format'
        ).get(id=program_id, status=ProgramStatus.ACTIVE)
    except Program.DoesNotExist:
        return None
    return serialize_program(program)


def get_programs_by_ids(program_ids: list[int]) -> list[dict]:
    if not program_ids:
        return []
    qs = Program.objects.filter(
        status=ProgramStatus.ACTIVE, id__in=program_ids
    ).select_related('direction', 'learning_format')
    by_id = {p.id: serialize_program(p) for p in qs}
    return [by_id[pid] for pid in program_ids if pid in by_id]
