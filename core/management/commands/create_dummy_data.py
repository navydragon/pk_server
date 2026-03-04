"""
Management команда для создания тестовых данных
Использование: python manage.py create_dummy_data
"""
import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker

from core.choices import (
    CourseBatchStatus,
    DirectionStatus,
    LearningFormatStatus,
    ProgramStatus,
    ProgramType,
)
from core.models import CourseBatch, Direction, LearningFormat, Program


class Command(BaseCommand):
    help = 'Создает тестовые данные для моделей каталога'

    def add_arguments(self, parser):
        parser.add_argument(
            '--directions',
            type=int,
            default=5,
            help='Количество направлений (по умолчанию: 5)',
        )
        parser.add_argument(
            '--formats',
            type=int,
            default=4,
            help='Количество форм обучения (по умолчанию: 4)',
        )
        parser.add_argument(
            '--programs',
            type=int,
            default=15,
            help='Количество программ (по умолчанию: 15)',
        )
        parser.add_argument(
            '--batches',
            type=int,
            default=30,
            help='Количество потоков (по умолчанию: 30)',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Удалить существующие данные перед созданием новых',
        )

    def handle(self, *args, **options):
        fake = Faker('ru_RU')
        directions_count = options['directions']
        formats_count = options['formats']
        programs_count = options['programs']
        batches_count = options['batches']
        clear = options['clear']

        if clear:
            self.stdout.write(self.style.WARNING('Удаление существующих данных...'))
            CourseBatch.objects.all().delete()
            Program.objects.all().delete()
            LearningFormat.objects.all().delete()
            Direction.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Существующие данные удалены.'))

        # Создание направлений
        self.stdout.write('Создание направлений...')
        directions = []
        direction_names = [
            'Программирование и IT',
            'Бизнес-анализ',
            'Финансы и бухгалтерия',
            'Маркетинг и реклама',
            'Управление проектами',
            'Дизайн',
            'HR и управление персоналом',
            'Юриспруденция',
        ]
        
        for i in range(directions_count):
            if i < len(direction_names):
                name = direction_names[i]
            else:
                # Генерируем уникальное название
                name = fake.sentence(nb_words=2).rstrip('.')
                while Direction.objects.filter(name=name).exists():
                    name = fake.sentence(nb_words=2).rstrip('.')
            
            direction, created = Direction.objects.get_or_create(
                name=name,
                defaults={
                    'short_description': fake.text(max_nb_chars=200) if random.random() > 0.3 else '',
                    'sort_order': i,
                    'status': random.choice([DirectionStatus.ACTIVE, DirectionStatus.ARCHIVED]),
                }
            )
            directions.append(direction)
            if created:
                self.stdout.write(f'  [OK] Создано направление: {direction.name}')
            else:
                self.stdout.write(f'  [SKIP] Направление уже существует: {direction.name}')

        # Создание форм обучения
        self.stdout.write('\nСоздание форм обучения...')
        formats = []
        format_names = [
            'Очный',
            'Онлайн с преподавателем',
            'Заочный',
            'Смешанный (очно-онлайн)',
        ]
        
        for i in range(formats_count):
            if i < len(format_names):
                name = format_names[i]
            else:
                # Генерируем уникальное название
                name = fake.sentence(nb_words=3).rstrip('.')
                while LearningFormat.objects.filter(name=name).exists():
                    name = fake.sentence(nb_words=3).rstrip('.')
            
            learning_format, created = LearningFormat.objects.get_or_create(
                name=name,
                defaults={
                    'short_description': fake.text(max_nb_chars=150) if random.random() > 0.3 else '',
                    'full_description': fake.text(max_nb_chars=500) if random.random() > 0.5 else '',
                    'sort_order': i,
                    'status': random.choice([LearningFormatStatus.ACTIVE, LearningFormatStatus.ARCHIVED]),
                }
            )
            formats.append(learning_format)
            if created:
                self.stdout.write(f'  [OK] Создана форма: {learning_format.name}')
            else:
                self.stdout.write(f'  [SKIP] Форма уже существует: {learning_format.name}')

        # Создание программ
        self.stdout.write('\nСоздание программ...')
        programs = []
        program_templates = [
            {
                'name_template': '{} для начинающих',
                'topics': ['Python', 'JavaScript', 'Java', 'C#', 'PHP', 'Go', 'Rust'],
            },
            {
                'name_template': 'Продвинутый курс по {}',
                'topics': ['Веб-разработке', 'Мобильной разработке', 'DevOps', 'Data Science'],
            },
            {
                'name_template': '{} и управление',
                'topics': ['Финансами', 'Проектами', 'Командами', 'Бизнес-процессами'],
            },
        ]

        for i in range(programs_count):
            direction = random.choice(directions)
            
            # Генерируем название программы
            if random.random() > 0.5 and program_templates:
                template = random.choice(program_templates)
                topic = random.choice(template['topics'])
                name = template['name_template'].format(topic)
            else:
                name = fake.sentence(nb_words=4).rstrip('.').title()
            
            # Выбираем одну форму обучения
            learning_format = random.choice(formats)
            
            program = Program.objects.create(
                name=name,
                direction=direction,
                program_type=random.choice([ProgramType.QUALIFICATION_UPGRADE, ProgramType.RETRAINING]),
                training_direction_code=fake.bothify(text='??-####', letters='ABCDEFGHIJKLMNOPQRSTUVWXYZ') if random.random() > 0.7 else '',
                lead=fake.text(max_nb_chars=300),
                about_description=fake.text(max_nb_chars=1000),
                curriculum=fake.text(max_nb_chars=1500),
                target_audience=fake.text(max_nb_chars=400),
                enrollment_process=fake.text(max_nb_chars=300) if random.random() > 0.3 else '',
                learning_format=learning_format,
                learning_format_comment=fake.text(max_nb_chars=200) if random.random() > 0.7 else '',
                hours_volume=random.choice([16, 24, 32, 40, 48, 72, 96, 120, 144]),
                duration=random.choice(['2 дня', '3 дня', '1 неделя', '2 недели', '1 месяц', '2 месяца', '3 месяца']),
                cost=random.choice(['15000', '25000', '35000', '45000', '60000', 'по запросу']),
                outcome=fake.text(max_nb_chars=200) if random.random() > 0.4 else '',
                requirements=fake.text(max_nb_chars=300) if random.random() > 0.5 else '',
                learning_outcomes=fake.text(max_nb_chars=400) if random.random() > 0.4 else '',
                status=random.choice([
                    ProgramStatus.DRAFT,
                    ProgramStatus.ACTIVE,
                    ProgramStatus.ARCHIVED,
                ]),
            )
            programs.append(program)
            self.stdout.write(f'  [OK] Создана программа: {program.name}')

        # Создание потоков
        self.stdout.write('\nСоздание потоков/наборов...')
        for i in range(batches_count):
            program = random.choice(programs)
            
            # Выбираем форму обучения для потока
            if program.learning_format:
                learning_format = program.learning_format
            else:
                # Если у программы нет формы, выбираем случайную
                learning_format = random.choice(formats)
            
            # Генерируем даты
            start_date = fake.date_between(start_date='today', end_date='+1y')
            end_date = start_date + timedelta(days=random.randint(7, 90))
            
            # Генерируем название потока (необязательное)
            batch_name = ''
            if random.random() > 0.5:
                batch_name = f'Поток {start_date.strftime("%Y-%m")}'
            
            batch = CourseBatch.objects.create(
                program=program,
                name=batch_name,
                start_date=start_date,
                end_date=end_date if random.random() > 0.2 else None,
                learning_format=learning_format,
                schedule=random.choice([
                    'Пн, Ср, Пт с 18:00 до 21:00',
                    'Вт, Чт с 19:00 до 22:00',
                    'Сб, Вс с 10:00 до 17:00',
                    'Ежедневно с 9:00 до 18:00',
                    'По индивидуальному расписанию',
                ]) if random.random() > 0.3 else '',
                seats_count=random.choice([10, 15, 20, 25, 30, None]) if random.random() > 0.2 else None,
                cost=random.choice(['15000 руб', '20000 руб', '25000 руб', '30000 руб', 'Бесплатно', 'По запросу', '0']) if random.random() > 0.2 else '0',
                status=random.choice([
                    CourseBatchStatus.ENROLLMENT_OPEN,
                    CourseBatchStatus.ENROLLMENT_CLOSED,
                    CourseBatchStatus.IN_PROGRESS,
                    CourseBatchStatus.COMPLETED,
                    CourseBatchStatus.CANCELLED,
                ]),
            )
            if i % 5 == 0:
                self.stdout.write(f'  [OK] Создано потоков: {i + 1}/{batches_count}')

        # Итоговая статистика
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(self.style.SUCCESS('Тестовые данные успешно созданы!'))
        self.stdout.write('=' * 50)
        self.stdout.write(f'Направлений: {Direction.objects.count()}')
        self.stdout.write(f'Форм обучения: {LearningFormat.objects.count()}')
        self.stdout.write(f'Программ: {Program.objects.count()}')
        self.stdout.write(f'Потоков/наборов: {CourseBatch.objects.count()}')
        self.stdout.write('=' * 50)
