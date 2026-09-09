"""
Management-команда для идемпотентного наполнения демо-данными.

Использование:
    python manage.py create_dummy_data
    python manage.py create_dummy_data --clear

Повторный запуск не плодит дубликаты: сущности обновляются по стабильным ключам.
"""
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from core.choices import (
    ApplicationStatus,
    CallbackRequestStatus,
    CallbackRequestType,
    CorporateRequestStatus,
    CourseBatchStatus,
    DirectionStatus,
    LearningFormatStatus,
    PreferredContact,
    ProgramStatus,
    ProgramType,
    StaffRole,
)
from core.models import (
    Application,
    CallbackRequest,
    CorporateRequest,
    CourseBatch,
    Direction,
    LearningFormat,
    Program,
    StaffProfile,
)
from publications.choices import PublicationStatus, PublicationType
from publications.models import Case, Category, Publication, Tag, Testimonial

User = get_user_model()

DEMO_PASSWORD = 'demo12345'

DEMO_USERS = (
    {
        'username': 'admin',
        'email': 'admin@demo.local',
        'full_name': 'Администратор Демо',
        'role': StaffRole.ADMINISTRATOR,
        'is_superuser': True,
        'is_staff': True,
    },
    {
        'username': 'methodist',
        'email': 'methodist@demo.local',
        'full_name': 'Методист Демо',
        'role': StaffRole.METHODIST,
        'is_superuser': False,
        'is_staff': True,
    },
    {
        'username': 'editor',
        'email': 'editor@demo.local',
        'full_name': 'Редактор Демо',
        'role': StaffRole.EDITOR,
        'is_superuser': False,
        'is_staff': True,
    },
)

DIRECTIONS = (
    ('Программирование и IT', 'Курсы по разработке, DevOps и данным', 0, DirectionStatus.ACTIVE),
    ('Бизнес-анализ', 'Аналитика процессов и требований', 1, DirectionStatus.ACTIVE),
    ('Финансы и бухгалтерия', 'Финансовый учёт и отчётность', 2, DirectionStatus.ACTIVE),
    ('Маркетинг и реклама', 'Digital-маркетинг и коммуникации', 3, DirectionStatus.ACTIVE),
    ('Управление проектами', 'PM, Agile и продуктовый подход', 4, DirectionStatus.ACTIVE),
    ('Дизайн', 'UX/UI и визуальные коммуникации', 5, DirectionStatus.ACTIVE),
    ('Архивное направление', 'Неактивное направление для демо фильтров', 6, DirectionStatus.ARCHIVED),
)

FORMATS = (
    ('Очный', 'Занятия в аудитории', 'Очное обучение с преподавателем', 0, LearningFormatStatus.ACTIVE),
    ('Онлайн с преподавателем', 'Вебинары в реальном времени', 'Онлайн-занятия по расписанию', 1, LearningFormatStatus.ACTIVE),
    ('Заочный', 'Самостоятельная работа с консультациями', 'Заочный формат с поддержкой куратора', 2, LearningFormatStatus.ACTIVE),
    ('Смешанный (очно-онлайн)', 'Часть занятий очно, часть онлайн', 'Blended learning', 3, LearningFormatStatus.ACTIVE),
)

PROGRAMS = (
    {
        'key': 'python-beginners',
        'name': 'Python для начинающих',
        'direction': 'Программирование и IT',
        'format': 'Онлайн с преподавателем',
        'program_type': ProgramType.QUALIFICATION_UPGRADE,
        'status': ProgramStatus.ACTIVE,
        'hours': 72,
        'duration': '2 месяца',
        'cost': '35000',
        'position': 1,
        'lead': 'Python с нуля: синтаксис, практика и первые проекты для новичков.',
        'audience': 'Начинающие разработчики и аналитики без опыта в Python.',
        'outcome': 'Удостоверение о повышении квалификации.',
        'requirements': 'Базовая компьютерная грамотность.',
    },
    {
        'key': 'js-web',
        'name': 'Веб-разработка на JavaScript',
        'direction': 'Программирование и IT',
        'format': 'Смешанный (очно-онлайн)',
        'program_type': ProgramType.QUALIFICATION_UPGRADE,
        'status': ProgramStatus.ACTIVE,
        'hours': 96,
        'duration': '3 месяца',
        'cost': '45000',
        'position': 2,
        'lead': 'Современный JavaScript для frontend: DOM, API и учебное портфолио.',
        'audience': 'Frontend-разработчики и верстальщики.',
        'outcome': 'Удостоверение + портфолио учебных проектов.',
        'requirements': 'Базовые знания HTML и CSS.',
    },
    {
        'key': 'devops',
        'name': 'Основы DevOps',
        'direction': 'Программирование и IT',
        'format': 'Онлайн с преподавателем',
        'program_type': ProgramType.RETRAINING,
        'status': ProgramStatus.ACTIVE,
        'hours': 120,
        'duration': '3 месяца',
        'cost': '60000',
        'position': 3,
        'lead': 'Переподготовка в DevOps: CI/CD, контейнеры и инфраструктура.',
        'audience': 'Системные администраторы и разработчики, переходящие в DevOps.',
        'outcome': 'Диплом о профессиональной переподготовке.',
        'requirements': 'Опыт работы с Linux и базовый скриптинг.',
    },
    {
        'key': 'ba-intro',
        'name': 'Бизнес-анализ с нуля',
        'direction': 'Бизнес-анализ',
        'format': 'Очный',
        'program_type': ProgramType.QUALIFICATION_UPGRADE,
        'status': ProgramStatus.ACTIVE,
        'hours': 48,
        'duration': '1 месяц',
        'cost': '28000',
        'position': 4,
        'lead': 'Введение в бизнес-анализ: требования, процессы и артефакты.',
        'audience': 'Специалисты, начинающие карьеру бизнес-аналитика.',
        'outcome': 'Удостоверение о повышении квалификации.',
        'requirements': 'Высшее или среднее профессиональное образование.',
    },
    {
        'key': 'ba-advanced',
        'name': 'Продвинутый бизнес-анализ',
        'direction': 'Бизнес-анализ',
        'format': 'Онлайн с преподавателем',
        'program_type': ProgramType.QUALIFICATION_UPGRADE,
        'status': ProgramStatus.DRAFT,
        'hours': 64,
        'duration': '1.5 месяца',
        'cost': '32000',
        'position': 5,
        'lead': 'Углублённый BA для действующих аналитиков.',
        'audience': 'Действующие бизнес-аналитики.',
        'outcome': 'Удостоверение о повышении квалификации.',
        'requirements': 'Опыт работы аналитиком от 1 года.',
    },
    {
        'key': 'finance-1c',
        'name': 'Бухгалтерский учёт и 1С',
        'direction': 'Финансы и бухгалтерия',
        'format': 'Очный',
        'program_type': ProgramType.RETRAINING,
        'status': ProgramStatus.ACTIVE,
        'hours': 144,
        'duration': '4 месяца',
        'cost': '55000',
        'position': 6,
        'lead': 'Переподготовка бухгалтера с практикой в 1С.',
        'audience': 'Бухгалтеры и экономисты транспортных компаний.',
        'outcome': 'Диплом о профессиональной переподготовке.',
        'requirements': 'Базовые знания бухгалтерского учёта.',
    },
    {
        'key': 'marketing-digital',
        'name': 'Digital-маркетинг',
        'direction': 'Маркетинг и реклама',
        'format': 'Онлайн с преподавателем',
        'program_type': ProgramType.QUALIFICATION_UPGRADE,
        'status': ProgramStatus.ACTIVE,
        'hours': 72,
        'duration': '2 месяца',
        'cost': '30000',
        'position': 7,
        'lead': 'Digital-продвижение: каналы, аналитика и кампании.',
        'audience': 'Маркетологи и специалисты по продвижению.',
        'outcome': 'Удостоверение о повышении квалификации.',
        'requirements': 'Опыт работы в маркетинге желателен.',
    },
    {
        'key': 'pm-agile',
        'name': 'Управление проектами (Agile)',
        'direction': 'Управление проектами',
        'format': 'Смешанный (очно-онлайн)',
        'program_type': ProgramType.QUALIFICATION_UPGRADE,
        'status': ProgramStatus.ACTIVE,
        'hours': 40,
        'duration': '3 недели',
        'cost': '25000',
        'position': 8,
        'lead': 'Короткий интенсив по Agile и управлению командой.',
        'audience': 'Руководители проектов и тимлиды.',
        'outcome': 'Удостоверение о повышении квалификации.',
        'requirements': 'Опыт участия в проектной работе.',
    },
    {
        'key': 'ux-ui',
        'name': 'UX/UI дизайн',
        'direction': 'Дизайн',
        'format': 'Онлайн с преподавателем',
        'program_type': ProgramType.QUALIFICATION_UPGRADE,
        'status': ProgramStatus.ACTIVE,
        'hours': 80,
        'duration': '2 месяца',
        'cost': '40000',
        'position': 9,
        'lead': 'UX/UI с нуля до учебного портфолио в Figma.',
        'audience': 'Дизайнеры и продуктовые специалисты.',
        'outcome': 'Удостоверение + учебное портфолио.',
        'requirements': 'Навыки работы в Figma или аналогичном инструменте.',
    },
    {
        'key': 'archived-pm',
        'name': 'Классический PM (архив)',
        'direction': 'Управление проектами',
        'format': 'Заочный',
        'program_type': ProgramType.QUALIFICATION_UPGRADE,
        'status': ProgramStatus.ARCHIVED,
        'hours': 36,
        'duration': '1 месяц',
        'cost': '20000',
        'position': 10,
        'lead': 'Архивная программа классического project management.',
        'audience': 'Менеджеры проектов.',
        'outcome': 'Удостоверение о повышении квалификации.',
        'requirements': 'Высшее образование.',
    },
)

BATCH_STATUSES = (
    CourseBatchStatus.ENROLLMENT_OPEN,
    CourseBatchStatus.ENROLLMENT_CLOSED,
    CourseBatchStatus.IN_PROGRESS,
    CourseBatchStatus.COMPLETED,
    CourseBatchStatus.CANCELLED,
)

APPLICATION_STATUSES = (
    ApplicationStatus.NEW,
    ApplicationStatus.IN_PROGRESS,
    ApplicationStatus.CONFIRMED,
    ApplicationStatus.REJECTED,
    ApplicationStatus.COMPLETED,
)

CORPORATE_STATUSES = (
    CorporateRequestStatus.NEW,
    CorporateRequestStatus.IN_PROGRESS,
    CorporateRequestStatus.QUOTE_SENT,
    CorporateRequestStatus.CLOSED,
)

CALLBACK_STATUSES = (
    CallbackRequestStatus.NEW,
    CallbackRequestStatus.PROCESSED,
    CallbackRequestStatus.CLOSED,
)

CONTENT_CATEGORIES = (
    ('Новости центра', 'novosti-centra', 'news', 0),
    ('Статьи экспертов', 'stati-ekspertov', 'article', 1),
    ('Корпоративное обучение', 'korporativnoe-obuchenie', 'case', 2),
)

CONTENT_TAGS = (
    ('Повышение квалификации', 'povyshenie-kvalifikacii'),
    ('Онлайн', 'onlayn'),
    ('Корпоративным клиентам', 'korporativnym-klientam'),
    ('IT', 'it'),
)


class Command(BaseCommand):
    help = (
        'Идемпотентно создаёт демо-пользователей и тестовые данные '
        'для каталога, CRM и контента'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Удалить ранее созданные демо-данные перед повторным наполнением',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options['clear']:
            self._clear_demo_data()

        self.stdout.write('Создание демо-пользователей...')
        users = self._ensure_users()

        self.stdout.write('\nСоздание каталога...')
        directions = self._ensure_directions()
        formats = self._ensure_formats()
        programs = self._ensure_programs(directions, formats)
        batches = self._ensure_batches(programs, formats)

        self.stdout.write('\nСоздание CRM-обращений...')
        applications = self._ensure_applications(programs, batches, users)
        corporate = self._ensure_corporate_requests(directions, programs, users)
        callbacks = self._ensure_callback_requests(users)

        self.stdout.write('\nСоздание контента...')
        categories, tags = self._ensure_content_taxonomy()
        publications = self._ensure_publications(categories, tags, users['editor'])
        cases = self._ensure_cases(categories, tags, users['editor'])
        testimonials = self._ensure_testimonials(users['editor'])

        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('Демо-данные готовы (команда идемпотентна).'))
        self.stdout.write('=' * 60)
        self.stdout.write('Пользователи /admin-panel/login/:')
        for spec in DEMO_USERS:
            self.stdout.write(
                f"  {spec['username']} / {DEMO_PASSWORD}  ({spec['full_name']}, {spec['role']})"
            )
        self.stdout.write('-' * 60)
        self.stdout.write(f'Направлений: {len(directions)}')
        self.stdout.write(f'Форм обучения: {len(formats)}')
        self.stdout.write(f'Программ: {len(programs)}')
        self.stdout.write(f'Потоков: {len(batches)}')
        self.stdout.write(f'Заявок слушателей: {len(applications)}')
        self.stdout.write(f'Корпоративных запросов: {len(corporate)}')
        self.stdout.write(f'Заказов звонка: {len(callbacks)}')
        self.stdout.write(f'Публикаций: {len(publications)}')
        self.stdout.write(f'Кейсов: {len(cases)}')
        self.stdout.write(f'Отзывов: {len(testimonials)}')
        self.stdout.write('=' * 60)

    def _clear_demo_data(self):
        self.stdout.write(self.style.WARNING('Очистка демо-данных...'))

        Application.objects.filter(is_test=True).delete()
        CallbackRequest.objects.filter(is_test=True).delete()
        CorporateRequest.objects.filter(is_test=True).delete()
        CourseBatch.objects.filter(is_test=True).delete()
        Program.objects.filter(is_test=True).delete()
        Direction.objects.filter(is_test=True).delete()
        LearningFormat.objects.filter(is_test=True).delete()
        Publication.objects.filter(is_test=True).delete()
        Case.objects.filter(is_test=True).delete()
        Testimonial.objects.filter(is_test=True).delete()
        Category.objects.filter(is_test=True).delete()
        Tag.objects.filter(is_test=True).delete()

        self.stdout.write(self.style.SUCCESS('Демо-данные удалены.'))

    def _ensure_users(self):
        users = {}
        for spec in DEMO_USERS:
            user, created = User.objects.get_or_create(
                username=spec['username'],
                defaults={
                    'email': spec['email'],
                    'is_staff': spec['is_staff'],
                    'is_superuser': spec['is_superuser'],
                    'is_active': True,
                },
            )
            user.email = spec['email']
            user.is_staff = spec['is_staff']
            user.is_superuser = spec['is_superuser']
            user.is_active = True
            user.set_password(DEMO_PASSWORD)
            user.save()

            StaffProfile.objects.update_or_create(
                user=user,
                defaults={
                    'full_name': spec['full_name'],
                    'role': spec['role'],
                    'is_active': True,
                },
            )
            users[spec['username']] = user
            mark = 'создан' if created else 'обновлён'
            self.stdout.write(f"  [OK] Пользователь {spec['username']} ({mark})")
        return users

    def _ensure_directions(self):
        result = {}
        for name, short_description, sort_order, status in DIRECTIONS:
            direction, created = Direction.objects.update_or_create(
                name=name,
                defaults={
                    'short_description': short_description,
                    'sort_order': sort_order,
                    'status': status,
                    'is_test': True,
                },
            )
            result[name] = direction
            mark = 'создано' if created else 'обновлено'
            self.stdout.write(f'  [OK] Направление «{name}» ({mark})')
        return result

    def _ensure_formats(self):
        result = {}
        for name, short_description, full_description, sort_order, status in FORMATS:
            learning_format, created = LearningFormat.objects.update_or_create(
                name=name,
                defaults={
                    'short_description': short_description,
                    'full_description': full_description,
                    'sort_order': sort_order,
                    'status': status,
                    'is_test': True,
                },
            )
            result[name] = learning_format
            mark = 'создана' if created else 'обновлена'
            self.stdout.write(f'  [OK] Форма «{name}» ({mark})')
        return result

    def _ensure_programs(self, directions, formats):
        result = {}
        for item in PROGRAMS:
            lead = item.get(
                'lead',
                f'Практическая программа «{item["name"]}» для специалистов.',
            )
            audience = item.get(
                'audience',
                'Специалисты и руководители, желающие повысить квалификацию.',
            )
            outcome = item.get(
                'outcome',
                'Удостоверение / диплом установленного образца.',
            )
            requirements = item.get(
                'requirements',
                'Среднее профессиональное или высшее образование.',
            )
            program, created = Program.objects.update_or_create(
                name=item['name'],
                defaults={
                    'direction': directions[item['direction']],
                    'program_type': item['program_type'],
                    'training_direction_code': f'DEMO-{item["key"].upper()}',
                    'lead': lead,
                    'about_description': (
                        f'Описание программы «{item["name"]}». '
                        'Демо-контент для проверки карточки и фильтров каталога.'
                    ),
                    'curriculum': (
                        '1. Введение\n'
                        '2. Основные темы\n'
                        '3. Практика\n'
                        '4. Итоговая аттестация'
                    ),
                    'target_audience': audience,
                    'enrollment_process': 'Заявка на сайте → консультация → договор → оплата.',
                    'learning_format': formats[item['format']],
                    'learning_format_comment': 'Возможна корпоративная группа.',
                    'hours_volume': item['hours'],
                    'duration': item['duration'],
                    'cost': item['cost'],
                    'outcome': outcome,
                    'requirements': requirements,
                    'learning_outcomes': 'Применение полученных компетенций в работе.',
                    'status': item['status'],
                    'position': item['position'],
                    'is_test': True,
                },
            )
            result[item['key']] = program
            mark = 'создана' if created else 'обновлена'
            self.stdout.write(f'  [OK] Программа «{item["name"]}» ({mark})')
        return result

    def _ensure_batches(self, programs, formats):
        result = []
        today = date.today()
        # offset_days, status_index, seats, cost_delta, schedule_index
        batch_specs = (
            (-45, CourseBatchStatus.COMPLETED, 12, 0, 0),  # прошедший — для админки
            (7, CourseBatchStatus.ENROLLMENT_OPEN, 15, 0, 0),
            (28, CourseBatchStatus.ENROLLMENT_CLOSED, 20, 5000, 1),
            (49, CourseBatchStatus.ENROLLMENT_OPEN, 25, -2000, 2),
        )
        schedules = (
            'Пн, Ср, Пт с 18:00 до 21:00',
            'Вт, Чт с 19:00 до 22:00',
            'Сб, Вс с 10:00 до 17:00',
        )
        index = 0
        for program_key, program in programs.items():
            for slot, (offset_days, status, seats, cost_delta, schedule_index) in enumerate(
                batch_specs, start=1
            ):
                index += 1
                start = today + timedelta(days=offset_days)
                end = start + timedelta(days=45)
                name = f'Демо-поток {program_key}-{slot}'
                learning_format = program.learning_format or next(iter(formats.values()))
                if program.cost.isdigit():
                    cost_value = str(max(0, int(program.cost) + cost_delta))
                else:
                    cost_value = program.cost
                batch, created = CourseBatch.objects.update_or_create(
                    program=program,
                    name=name,
                    defaults={
                        'start_date': start,
                        'end_date': end,
                        'learning_format': learning_format,
                        'schedule': schedules[schedule_index],
                        'seats_count': seats,
                        'cost': cost_value,
                        'status': status,
                        'is_test': True,
                    },
                )
                result.append(batch)
                mark = 'создан' if created else 'обновлён'
                if index % 5 == 1 or created:
                    self.stdout.write(f'  [OK] {name} ({mark})')
        self.stdout.write(f'  Всего потоков: {len(result)}')
        return result

    def _ensure_applications(self, programs, batches, users):
        result = []
        program_list = list(programs.values())
        batch_by_program = {}
        for batch in batches:
            batch_by_program.setdefault(batch.program_id, []).append(batch)

        assignees = [users['admin'], users['methodist'], None]
        names = (
            'Иванова Анна Сергеевна',
            'Петров Дмитрий Игоревич',
            'Сидорова Мария Алексеевна',
            'Козлов Алексей Викторович',
            'Морозова Елена Павловна',
            'Волков Иван Николаевич',
            'Соколова Ольга Дмитриевна',
            'Лебедев Павел Андреевич',
        )
        now = timezone.now()

        for i in range(1, 26):
            program = program_list[(i - 1) % len(program_list)]
            program_batches = batch_by_program.get(program.id, [])
            batch = program_batches[(i - 1) % len(program_batches)] if program_batches else None
            email = f'listener{i:02d}@demo.local'
            status = APPLICATION_STATUSES[(i - 1) % len(APPLICATION_STATUSES)]
            preferred = (
                PreferredContact.PHONE,
                PreferredContact.EMAIL,
                PreferredContact.MESSENGER,
                '',
            )[(i - 1) % 4]
            application, created = Application.objects.update_or_create(
                email=email,
                defaults={
                    'full_name': names[(i - 1) % len(names)],
                    'program': program,
                    'batch': batch,
                    'phone': f'+79002{i:06d}',
                    'preferred_contact': preferred,
                    'comment': 'Демо-заявка слушателя' if i % 3 else '',
                    'status': status,
                    'admin_comment': 'Взято в работу' if status != ApplicationStatus.NEW else '',
                    'assigned_to': assignees[(i - 1) % len(assignees)],
                    'is_test': True,
                },
            )
            Application.objects.filter(pk=application.pk).update(
                created_at=now - timedelta(days=(i * 3) % 90, hours=i % 12),
                updated_at=now - timedelta(days=(i * 2) % 60),
            )
            result.append(application)
            if created or i % 5 == 0:
                mark = 'создана' if created else 'обновлена'
                self.stdout.write(f'  [OK] Заявка {email} ({mark})')
        return result

    def _ensure_corporate_requests(self, directions, programs, users):
        result = []
        orgs = (
            'ООО «СеверТех»',
            'АО «Городские сети»',
            'ПАО «ИнвестПром»',
            'ООО «МедСервис»',
            'ЗАО «Логистика Плюс»',
            'ООО «АгроКомплекс»',
            'ИП Кузнецов',
            'ООО «СтройАльянс»',
            'АО «ФинансГрупп»',
            'ООО «Ритейл Маркет»',
            'ООО «ЭнергоСервис»',
            'АО «ТрансЛайн»',
        )
        now = timezone.now()
        direction_list = [directions[name] for name, *_ in DIRECTIONS if name != 'Архивное направление']
        program_list = [p for p in programs.values() if p.status == ProgramStatus.ACTIVE]
        assignees = [users['admin'], users['methodist'], None]

        for i, org in enumerate(orgs, start=1):
            email = f'corp{i:02d}@demo.local'
            status = CORPORATE_STATUSES[(i - 1) % len(CORPORATE_STATUSES)]
            request_obj, created = CorporateRequest.objects.update_or_create(
                email=email,
                defaults={
                    'organization_name': org,
                    'contact_name': f'Контактное лицо {i}',
                    'contact_position': 'HR-директор' if i % 2 else 'Руководитель обучения',
                    'phone': f'+79003{i:06d}',
                    'topics': 'Корпоративное обучение сотрудников, групповой формат',
                    'employees_count': 5 + i * 3,
                    'desired_dates': 'II–III квартал' if i % 2 else 'В течение месяца',
                    'comment': 'Демо корпоративный запрос' if i % 2 else '',
                    'status': status,
                    'admin_comment': 'КП в работе' if status != CorporateRequestStatus.NEW else '',
                    'assigned_to': assignees[(i - 1) % len(assignees)],
                    'is_test': True,
                },
            )
            d_start = (i - 1) % len(direction_list)
            p_start = (i - 1) % len(program_list)
            request_obj.directions.set([
                direction_list[d_start],
                direction_list[(d_start + 1) % len(direction_list)],
            ])
            request_obj.programs.set([
                program_list[p_start],
                program_list[(p_start + 1) % len(program_list)],
            ])
            CorporateRequest.objects.filter(pk=request_obj.pk).update(
                created_at=now - timedelta(days=(i * 4) % 80, hours=i % 10),
                updated_at=now - timedelta(days=(i * 2) % 40),
            )
            result.append(request_obj)
            mark = 'создан' if created else 'обновлён'
            self.stdout.write(f'  [OK] Корп. запрос {org} ({mark})')
        return result

    def _ensure_callback_requests(self, users):
        result = []
        now = timezone.now()
        people = (
            'Алексей',
            'Марина',
            'Игорь',
            'Наталья',
            'Сергей',
            'Юлия',
            'Андрей',
            'Екатерина',
            'Роман',
            'Татьяна',
            'Кирилл',
            'Валерия',
            'Денис',
            'Анна',
            'Максим',
        )
        assignees = [users['admin'], users['methodist'], None]

        for i, name in enumerate(people, start=1):
            phone = f'+79001{i:06d}'
            email = f'callback{i:02d}@demo.local' if i % 2 else ''
            status = CALLBACK_STATUSES[(i - 1) % len(CALLBACK_STATUSES)]
            request_type = (
                CallbackRequestType.INDIVIDUAL
                if i % 2
                else CallbackRequestType.ORGANIZATION
            )
            request_obj, created = CallbackRequest.objects.update_or_create(
                phone=phone,
                defaults={
                    'name': name,
                    'email': email,
                    'request_type': request_type,
                    'comment': 'Просьба перезвонить по программе' if i % 3 else '',
                    'status': status,
                    'admin_comment': 'Перезвонили' if status != CallbackRequestStatus.NEW else '',
                    'assigned_to': assignees[(i - 1) % len(assignees)],
                    'is_test': True,
                },
            )
            CallbackRequest.objects.filter(pk=request_obj.pk).update(
                created_at=now - timedelta(days=(i * 2) % 45, hours=i % 8),
                updated_at=now - timedelta(days=i % 20),
            )
            result.append(request_obj)
            if created or i % 5 == 0:
                mark = 'создан' if created else 'обновлён'
                self.stdout.write(f'  [OK] Звонок {phone} ({mark})')
        return result

    def _ensure_content_taxonomy(self):
        categories = {}
        for name, slug, category_type, sort_order in CONTENT_CATEGORIES:
            category, created = Category.objects.update_or_create(
                slug=slug,
                defaults={
                    'name': name,
                    'description': f'Демо-категория: {name}',
                    'sort_order': sort_order,
                    'category_type': category_type,
                    'is_test': True,
                },
            )
            categories[slug] = category
            mark = 'создана' if created else 'обновлена'
            self.stdout.write(f'  [OK] Категория «{name}» ({mark})')

        tags = {}
        for name, slug in CONTENT_TAGS:
            tag, created = Tag.objects.update_or_create(
                slug=slug,
                defaults={'name': name, 'is_test': True},
            )
            tags[slug] = tag
            mark = 'создан' if created else 'обновлён'
            self.stdout.write(f'  [OK] Тег «{name}» ({mark})')
        return categories, tags

    def _ensure_publications(self, categories, tags, editor):
        result = []
        now = timezone.now()
        items = (
            {
                'slug': 'demo-otkrytie-nabora-python',
                'type': PublicationType.NEWS,
                'title': 'Открыт набор на курс Python для начинающих',
                'status': PublicationStatus.PUBLISHED,
                'featured': True,
                'category': 'novosti-centra',
                'days_ago': 3,
            },
            {
                'slug': 'demo-novyy-format-online',
                'type': PublicationType.NEWS,
                'title': 'Запущен новый онлайн-формат обучения',
                'status': PublicationStatus.PUBLISHED,
                'featured': False,
                'category': 'novosti-centra',
                'days_ago': 12,
            },
            {
                'slug': 'demo-chernovik-novosti',
                'type': PublicationType.NEWS,
                'title': 'Черновик новости (демо)',
                'status': PublicationStatus.DRAFT,
                'featured': False,
                'category': 'novosti-centra',
                'days_ago': None,
            },
            {
                'slug': 'demo-kak-vybrat-programmu',
                'type': PublicationType.ARTICLE,
                'title': 'Как выбрать программу повышения квалификации',
                'status': PublicationStatus.PUBLISHED,
                'featured': True,
                'category': 'stati-ekspertov',
                'days_ago': 20,
            },
            {
                'slug': 'demo-korporativnoe-obuchenie',
                'type': PublicationType.ARTICLE,
                'title': 'Корпоративное обучение: с чего начать',
                'status': PublicationStatus.PUBLISHED,
                'featured': False,
                'category': 'stati-ekspertov',
                'days_ago': 35,
            },
            {
                'slug': 'demo-moderaciya-stati',
                'type': PublicationType.ARTICLE,
                'title': 'Статья на модерации (демо)',
                'status': PublicationStatus.ON_MODERATION,
                'featured': False,
                'category': 'stati-ekspertov',
                'days_ago': None,
            },
            {
                'slug': 'demo-arhiv-stati',
                'type': PublicationType.ARTICLE,
                'title': 'Архивная статья (демо)',
                'status': PublicationStatus.ARCHIVED,
                'featured': False,
                'category': 'stati-ekspertov',
                'days_ago': 120,
            },
        )

        for sort_order, item in enumerate(items):
            published_at = None
            if item['days_ago'] is not None:
                published_at = now - timedelta(days=item['days_ago'])
            publication, created = Publication.objects.update_or_create(
                slug=item['slug'],
                defaults={
                    'type': item['type'],
                    'title': item['title'],
                    'short_description': f'Краткое описание: {item["title"]}',
                    'content': (
                        f'<p>Демо-содержимое публикации «{item["title"]}».</p>'
                        '<p>Используется для проверки админ-панели и публичного API.</p>'
                    ),
                    'status': item['status'],
                    'published_at': published_at,
                    'is_featured': item['featured'],
                    'sort_order': sort_order,
                    'created_by': editor,
                    'updated_by': editor,
                    'meta_title': item['title'][:255],
                    'meta_description': f'SEO описание для {item["title"]}',
                    'is_test': True,
                },
            )
            publication.categories.set([categories[item['category']]])
            publication.tags.set([tags['povyshenie-kvalifikacii'], tags['onlayn']])
            result.append(publication)
            mark = 'создана' if created else 'обновлена'
            self.stdout.write(f'  [OK] Публикация «{item["title"]}» ({mark})')
        return result

    def _ensure_cases(self, categories, tags, editor):
        result = []
        now = timezone.now()
        items = (
            {
                'slug': 'demo-case-severtech',
                'title': 'Обучение команды разработки в «СеверТех»',
                'status': PublicationStatus.PUBLISHED,
                'featured': True,
                'days_ago': 40,
                'company': 'ООО «СеверТех»',
            },
            {
                'slug': 'demo-case-medservice',
                'title': 'Корпоративный курс для HR «МедСервис»',
                'status': PublicationStatus.PUBLISHED,
                'featured': False,
                'days_ago': 70,
                'company': 'ООО «МедСервис»',
            },
            {
                'slug': 'demo-case-draft',
                'title': 'Черновик кейса (демо)',
                'status': PublicationStatus.DRAFT,
                'featured': False,
                'days_ago': None,
                'company': 'Демо-компания',
            },
        )
        for sort_order, item in enumerate(items):
            published_at = None
            if item['days_ago'] is not None:
                published_at = now - timedelta(days=item['days_ago'])
            case, created = Case.objects.update_or_create(
                slug=item['slug'],
                defaults={
                    'title': item['title'],
                    'short_description': f'Кратко о кейсе: {item["title"]}',
                    'content': f'<p>Подробное описание кейса «{item["title"]}».</p>',
                    'client_company': item['company'],
                    'client_industry': 'IT / услуги',
                    'services': 'Корпоративные программы повышения квалификации',
                    'results_short': 'Обучено 40+ сотрудников',
                    'results_detailed': 'Проведены очные и онлайн-модули, NPS 9.1.',
                    'metrics': '40 слушателей, 2 потока, 96 часов',
                    'status': item['status'],
                    'published_at': published_at,
                    'is_featured': item['featured'],
                    'sort_order': sort_order,
                    'created_by': editor,
                    'updated_by': editor,
                    'meta_title': item['title'][:255],
                    'meta_description': f'Кейс {item["company"]}',
                    'is_test': True,
                },
            )
            case.categories.set([categories['korporativnoe-obuchenie']])
            case.tags.set([tags['korporativnym-klientam'], tags['it']])
            result.append(case)
            mark = 'создан' if created else 'обновлён'
            self.stdout.write(f'  [OK] Кейс «{item["title"]}» ({mark})')
        return result

    def _ensure_testimonials(self, editor):
        result = []
        now = timezone.now()
        items = (
            {
                'slug': 'demo-testimonial-ivanova',
                'person_name': 'Иванова А. С.',
                'person_position': 'Руководитель отдела',
                'company_name': 'ООО «СеверТех»',
                'quote': 'Программа помогла команде быстро выйти на единый уровень компетенций.',
                'rating': 5,
                'status': PublicationStatus.PUBLISHED,
                'featured': True,
                'days_ago': 15,
            },
            {
                'slug': 'demo-testimonial-petrov',
                'person_name': 'Петров Д. И.',
                'person_position': 'HR BP',
                'company_name': 'АО «Городские сети»',
                'quote': 'Удобный формат и понятная отчётность для корпоративного заказчика.',
                'rating': 4,
                'status': PublicationStatus.PUBLISHED,
                'featured': False,
                'days_ago': 28,
            },
            {
                'slug': 'demo-testimonial-moderation',
                'person_name': 'Сидорова М. А.',
                'person_position': 'Специалист',
                'company_name': '',
                'quote': 'Отзыв на модерации — демо-запись.',
                'rating': 5,
                'status': PublicationStatus.ON_MODERATION,
                'featured': False,
                'days_ago': None,
            },
            {
                'slug': 'demo-testimonial-draft',
                'person_name': 'Козлов А. В.',
                'person_position': 'Менеджер',
                'company_name': 'ООО «Ритейл Маркет»',
                'quote': 'Черновик отзыва для проверки статусов.',
                'rating': 3,
                'status': PublicationStatus.DRAFT,
                'featured': False,
                'days_ago': None,
            },
        )
        for sort_order, item in enumerate(items):
            published_at = None
            if item['days_ago'] is not None:
                published_at = now - timedelta(days=item['days_ago'])
            testimonial, created = Testimonial.objects.update_or_create(
                slug=item['slug'],
                defaults={
                    'person_name': item['person_name'],
                    'person_position': item['person_position'],
                    'company_name': item['company_name'],
                    'quote': item['quote'],
                    'rating': item['rating'],
                    'status': item['status'],
                    'published_at': published_at,
                    'is_featured': item['featured'],
                    'sort_order': sort_order,
                    'created_by': editor,
                    'updated_by': editor,
                    'is_test': True,
                },
            )
            result.append(testimonial)
            mark = 'создан' if created else 'обновлён'
            self.stdout.write(f'  [OK] Отзыв «{item["person_name"]}» ({mark})')
        return result
