"""
Импорт программ из CSV-файла `core/programs.csv`.

Запуск:
    python manage.py import_programs
    python manage.py import_programs --path core/programs.csv
"""
import csv
import re
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from core.choices import (
    DirectionStatus,
    LearningFormatStatus,
    ProgramStatus,
    ProgramType,
)
from core.models import Direction, LearningFormat, Program


class Command(BaseCommand):
    help = 'Импортирует программы из CSV-файла (по умолчанию: core/programs.csv)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--path',
            type=str,
            default='core/programs.csv',
            help='Путь к CSV-файлу с программами (по умолчанию: core/programs.csv)',
        )
        parser.add_argument(
            '--clear-programs',
            action='store_true',
            help='Удалить все существующие программы перед импортом',
        )

    def handle(self, *args, **options):
        csv_path = options['path']
        clear_programs = options['clear_programs']

        file_path = Path(csv_path)
        if not file_path.is_absolute():
            file_path = Path(settings.BASE_DIR) / file_path

        if not file_path.exists():
            raise CommandError(f'CSV-файл не найден: {file_path}')

        if clear_programs:
            self.stdout.write(self.style.WARNING('Удаление существующих программ...'))
            deleted_count, _ = Program.objects.all().delete()
            self.stdout.write(self.style.SUCCESS(f'Удалено программ: {deleted_count}'))

        self.stdout.write(f'Чтение CSV-файла: {file_path}')

        created_count = 0
        updated_count = 0
        skipped_count = 0

        with file_path.open('r', encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f, delimiter=';')

            for row in reader:
                try:
                    program, created = self._import_row(row)
                except Exception as exc:
                    skipped_count += 1
                    self.stderr.write(
                        self.style.ERROR(
                            f'Ошибка при обработке строки с id={row.get("id")}: {exc}'
                        )
                    )
                    continue

                if created:
                    created_count += 1
                else:
                    updated_count += 1

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Импорт завершён'))
        self.stdout.write(f'Создано программ: {created_count}')
        self.stdout.write(f'Обновлено программ: {updated_count}')
        self.stdout.write(f'Пропущено строк (ошибки): {skipped_count}')

    def _parse_program_type(self, value: str) -> str:
        if not value:
            return ProgramType.QUALIFICATION_UPGRADE

        v = value.strip().lower()
        mapping = {
            'пк': ProgramType.QUALIFICATION_UPGRADE,
            'pk': ProgramType.QUALIFICATION_UPGRADE,
            'повышение квалификации': ProgramType.QUALIFICATION_UPGRADE,
            'пп': ProgramType.RETRAINING,
            'pp': ProgramType.RETRAINING,
            'переподготовка': ProgramType.RETRAINING,
        }

        if v in mapping:
            return mapping[v]

        # На всякий случай не падаем, а считаем как повышение квалификации
        return ProgramType.QUALIFICATION_UPGRADE

    def _parse_status(self, value: str) -> str:
        if not value:
            return ProgramStatus.ACTIVE

        v = value.strip().lower()
        if v in {ProgramStatus.DRAFT, ProgramStatus.ACTIVE, ProgramStatus.ARCHIVED}:
            return v
        return ProgramStatus.ACTIVE

    def _parse_hours(self, value: str) -> int:
        if not value:
            return 0

        digits = re.sub(r'\D', '', value)
        if not digits:
            return 0
        try:
            return int(digits)
        except ValueError:
            return 0

    def _get_or_create_direction(self, name: str) -> Direction:
        name = (name or '').strip()
        if not name:
            raise ValueError('Не задано название направления (direction_name)')

        direction, _ = Direction.objects.get_or_create(
            name=name,
            defaults={
                'short_description': '',
                'sort_order': 0,
                'status': DirectionStatus.ACTIVE,
            },
        )
        return direction

    def _get_or_create_learning_format(self, name: str) -> LearningFormat | None:
        name = (name or '').strip()
        if not name:
            return None

        learning_format, _ = LearningFormat.objects.get_or_create(
            name=name,
            defaults={
                'short_description': '',
                'full_description': '',
                'sort_order': 0,
                'status': LearningFormatStatus.ACTIVE,
            },
        )
        return learning_format

    def _import_row(self, row: dict) -> tuple[Program, bool]:
        """
        Импорт одной строки CSV.

        Ожидаемые поля CSV:
        id;direction_name;name;training_direction_code;program_type;learning_format;
        hours_volume;cost;about_description;lead;duration;status
        """
        csv_id_raw = row.get('id', '')
        try:
            position = int(csv_id_raw) if csv_id_raw else 0
        except (ValueError, TypeError):
            position = 0

        direction_name = row.get('direction_name', '')
        name = (row.get('name') or '').strip()
        training_direction_code = (row.get('training_direction_code') or '').strip()
        program_type_raw = row.get('program_type', '')
        learning_format_name = row.get('learning_format', '')
        hours_volume_raw = row.get('hours_volume', '')
        cost = (row.get('cost') or '').strip()
        about_description = (row.get('about_description') or '').strip()
        lead = (row.get('lead') or '').strip()
        duration = (row.get('duration') or '').strip()
        status_raw = row.get('status', '')

        if not name:
            raise ValueError('Не задано название программы (name)')

        direction = self._get_or_create_direction(direction_name)
        learning_format = self._get_or_create_learning_format(learning_format_name)

        program_type = self._parse_program_type(program_type_raw)
        status = self._parse_status(status_raw)
        hours_volume = self._parse_hours(hours_volume_raw)

        # Заполняем обязательные текстовые поля простыми значениями,
        # чтобы можно было отредактировать позже в админке.
        curriculum = about_description or 'Учебный план будет уточнён.'
        target_audience = 'Целевая аудитория будет уточнена.'

        program, created = Program.objects.update_or_create(
            name=name,
            defaults={
                'position': position,
                'direction': direction,
                'program_type': program_type,
                'training_direction_code': training_direction_code,
                'lead': lead or about_description[:300] or name,
                'about_description': about_description or lead or name,
                'curriculum': curriculum,
                'target_audience': target_audience,
                'enrollment_process': '',
                'learning_format': learning_format,
                'learning_format_comment': '',
                'hours_volume': hours_volume,
                'duration': duration or (hours_volume_raw or ''),
                'cost': cost,
                'outcome': '',
                'requirements': '',
                'learning_outcomes': '',
                'status': status,
            },
        )

        action = 'Создана' if created else 'Обновлена'
        self.stdout.write(f'[{action}] программа: {program.name}')

        return program, created

