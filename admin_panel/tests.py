from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from core.choices import (
    ApplicationStatus,
    CallbackRequestStatus,
    CorporateRequestStatus,
    CourseBatchStatus,
    LearningFormatStatus,
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

User = get_user_model()


def create_staff_user(username, password='testpass123', role=StaffRole.ADMINISTRATOR):
    """Создаёт пользователя с профилем сотрудника."""
    user = User.objects.create_user(username=username, password=password)
    StaffProfile.objects.create(
        user=user,
        full_name=username.title(),
        role=role,
    )
    return user


def create_test_program(direction_name='Тестовое направление'):
    """Создаёт тестовую программу с направлением."""
    direction, _ = Direction.objects.get_or_create(
        name=direction_name,
        defaults={'status': 'active'}
    )
    return Program.objects.create(
        name='Тестовая программа',
        direction=direction,
        program_type=ProgramType.QUALIFICATION_UPGRADE,
        lead='Лид',
        about_description='Описание',
        curriculum='План',
        target_audience='Аудитория',
        hours_volume=72,
        duration='2 месяца',
        cost='10000 руб',
        status=ProgramStatus.ACTIVE
    )


def create_test_batch(program=None, format_name='Очная'):
    """Создаёт тестовый поток."""
    if program is None:
        program = create_test_program()
    learning_format, _ = LearningFormat.objects.get_or_create(
        name=format_name,
        defaults={'status': LearningFormatStatus.ACTIVE}
    )
    return CourseBatch.objects.create(
        program=program,
        learning_format=learning_format,
        start_date='2025-03-01',
        status=CourseBatchStatus.ENROLLMENT_OPEN
    )


class ApplicationModelTests(TestCase):
    """Тесты модели Application."""

    def test_application_str_representation(self):
        program = create_test_program()
        application = Application.objects.create(
            full_name='Иванов Иван Иванович',
            program=program,
            email='test@example.com',
            phone='+7 999 123-45-67'
        )
        self.assertIn('Иванов Иван Иванович', str(application))
        self.assertIn(program.name, str(application))

    def test_application_default_status(self):
        program = create_test_program()
        application = Application.objects.create(
            full_name='Петров Пётр',
            program=program,
            email='petrov@example.com',
            phone='+7 999 111-22-33'
        )
        self.assertEqual(application.status, ApplicationStatus.NEW)

    def test_application_created_at_auto_set(self):
        program = create_test_program()
        application = Application.objects.create(
            full_name='Сидоров Сидор',
            program=program,
            email='sidorov@example.com',
            phone='+7 999 444-55-66'
        )
        self.assertIsNotNone(application.created_at)
        self.assertIsNotNone(application.updated_at)


class CorporateRequestModelTests(TestCase):
    """Тесты модели CorporateRequest."""

    def test_default_status_and_str(self):
        req = CorporateRequest.objects.create(
            organization_name='ООО Ромашка',
            contact_name='Иванов Иван',
            phone='+7 999 111-11-11',
            email='corp@example.com',
            topics='Python, Excel',
            employees_count=15,
        )
        self.assertEqual(req.status, CorporateRequestStatus.NEW)
        self.assertIn('ООО Ромашка', str(req))
        self.assertIsNotNone(req.updated_at)


class ApplicationCRUDViewTests(TestCase):
    """Тесты CRUD представлений для заявок."""

    def setUp(self):
        self.client = Client()
        self.user = create_staff_user('admin', role=StaffRole.ADMINISTRATOR)
        self.program = create_test_program()
        self.batch = create_test_batch(self.program)

    def test_application_list_requires_login(self):
        url = reverse('admin_panel:application_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_application_list_renders_for_authenticated_user(self):
        self.client.login(username='admin', password='testpass123')
        url = reverse('admin_panel:application_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('applications', response.context)

    def test_application_create_success(self):
        self.client.login(username='admin', password='testpass123')
        url = reverse('admin_panel:application_create')
        data = {
            'full_name': 'Новый Слушатель',
            'program': self.program.pk,
            'email': 'new@example.com',
            'phone': '+7 999 000-00-00',
            'status': ApplicationStatus.NEW,
            'comment': '',
            'admin_comment': '',
            'preferred_contact': '',
        }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Application.objects.count(), 1)
        app = Application.objects.first()
        self.assertEqual(app.full_name, 'Новый Слушатель')
        self.assertEqual(app.email, 'new@example.com')

    def test_application_update_success(self):
        application = Application.objects.create(
            full_name='Старое Имя',
            program=self.program,
            email='old@example.com',
            phone='+7 999 111-11-11'
        )
        self.client.login(username='admin', password='testpass123')
        url = reverse('admin_panel:application_edit', args=[application.pk])
        data = {
            'full_name': 'Обновлённое Имя',
            'program': self.program.pk,
            'email': 'updated@example.com',
            'phone': '+7 999 222-22-22',
            'status': ApplicationStatus.IN_PROGRESS,
            'comment': '',
            'admin_comment': '',
            'preferred_contact': '',
        }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        application.refresh_from_db()
        self.assertEqual(application.full_name, 'Обновлённое Имя')
        self.assertEqual(application.status, ApplicationStatus.IN_PROGRESS)

    def test_application_delete_success(self):
        application = Application.objects.create(
            full_name='На удаление',
            program=self.program,
            email='delete@example.com',
            phone='+7 999 333-33-33'
        )
        self.client.login(username='admin', password='testpass123')
        url = reverse('admin_panel:application_delete', args=[application.pk])
        response = self.client.post(url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Application.objects.filter(pk=application.pk).exists())

    def test_application_export_csv(self):
        Application.objects.create(
            full_name='Экспорт Тест',
            program=self.program,
            email='export@example.com',
            phone='+7 999 777-77-77',
        )
        self.client.login(username='admin', password='testpass123')
        url = reverse('admin_panel:application_export')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/csv', response['Content-Type'])
        self.assertIn('Экспорт Тест'.encode('utf-8'), response.content)

    def test_application_quick_status(self):
        application = Application.objects.create(
            full_name='Статус Тест',
            program=self.program,
            email='status@example.com',
            phone='+7 999 888-88-88',
        )
        self.client.login(username='admin', password='testpass123')
        url = reverse('admin_panel:application_quick_status', args=[application.pk])
        response = self.client.post(url, {'status': ApplicationStatus.IN_PROGRESS}, follow=True)
        self.assertEqual(response.status_code, 200)
        application.refresh_from_db()
        self.assertEqual(application.status, ApplicationStatus.IN_PROGRESS)

    def test_application_filter_by_status(self):
        Application.objects.create(
            full_name='Новая',
            program=self.program,
            email='new@example.com',
            phone='+7 999 101-01-01',
            status=ApplicationStatus.NEW,
        )
        Application.objects.create(
            full_name='В работе',
            program=self.program,
            email='work@example.com',
            phone='+7 999 202-02-02',
            status=ApplicationStatus.IN_PROGRESS,
        )
        self.client.login(username='admin', password='testpass123')
        url = reverse('admin_panel:application_list')
        response = self.client.get(url, {'status': ApplicationStatus.NEW})
        self.assertEqual(response.status_code, 200)
        apps = list(response.context['applications'])
        self.assertEqual(len(apps), 1)
        self.assertEqual(apps[0].full_name, 'Новая')


class ApplicationFormTests(TestCase):
    """Тесты формы заявки."""

    def setUp(self):
        self.program = create_test_program('Направление 1')
        self.batch = create_test_batch(self.program)
        self.other_program = create_test_program('Направление 2')
        self.other_batch = create_test_batch(self.other_program, format_name='Онлайн')

    def test_application_form_valid_data(self):
        from admin_panel.forms import ApplicationForm

        data = {
            'full_name': 'Валидный Пользователь',
            'program': self.program.pk,
            'batch': self.batch.pk,
            'email': 'valid@example.com',
            'phone': '+7 999 555-55-55',
            'status': ApplicationStatus.NEW,
            'comment': '',
            'admin_comment': '',
            'preferred_contact': '',
        }
        form = ApplicationForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_application_form_batch_must_belong_to_program(self):
        from admin_panel.forms import ApplicationForm

        data = {
            'full_name': 'Невалидный Выбор',
            'program': self.program.pk,
            'batch': self.other_batch.pk,
            'email': 'invalid@example.com',
            'phone': '+7 999 666-66-66',
            'status': ApplicationStatus.NEW,
            'comment': '',
            'admin_comment': '',
            'preferred_contact': '',
        }
        form = ApplicationForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('batch', form.errors)


class CallbackRequestCRUDViewTests(TestCase):
    """Тесты CRUD представлений для запросов обратного звонка."""

    def setUp(self):
        self.client = Client()
        self.user = create_staff_user('admin', role=StaffRole.ADMINISTRATOR)

    def test_callbackrequest_list_requires_login(self):
        url = reverse('admin_panel:callbackrequest_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_callbackrequest_list_renders_for_authenticated_user(self):
        self.client.login(username='admin', password='testpass123')
        url = reverse('admin_panel:callbackrequest_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('callback_requests', response.context)

    def test_callbackrequest_create_success(self):
        self.client.login(username='admin', password='testpass123')
        url = reverse('admin_panel:callbackrequest_create')
        data = {
            'name': 'Иван Иванов',
            'phone': '+7 999 123-45-67',
            'email': 'ivan@example.com',
            'status': CallbackRequestStatus.NEW,
            'request_type': '',
            'comment': '',
            'admin_comment': '',
        }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(CallbackRequest.objects.count(), 1)
        req = CallbackRequest.objects.first()
        self.assertEqual(req.name, 'Иван Иванов')
        self.assertEqual(req.email, 'ivan@example.com')

    def test_callbackrequest_update_success(self):
        req = CallbackRequest.objects.create(
            name='Старое Имя',
            phone='+7 999 000-00-00',
            email='old@example.com',
        )
        self.client.login(username='admin', password='testpass123')
        url = reverse('admin_panel:callbackrequest_edit', args=[req.pk])
        data = {
            'name': 'Обновлённое Имя',
            'phone': '+7 999 111-11-11',
            'email': 'updated@example.com',
            'status': CallbackRequestStatus.PROCESSED,
            'request_type': '',
            'comment': 'Связались',
            'admin_comment': '',
        }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        req.refresh_from_db()
        self.assertEqual(req.name, 'Обновлённое Имя')
        self.assertEqual(req.email, 'updated@example.com')
        self.assertEqual(req.status, CallbackRequestStatus.PROCESSED)

    def test_callbackrequest_delete_success(self):
        req = CallbackRequest.objects.create(
            name='На удаление',
            phone='+7 999 222-22-22',
            email='delete@example.com',
        )
        self.client.login(username='admin', password='testpass123')
        url = reverse('admin_panel:callbackrequest_delete', args=[req.pk])
        response = self.client.post(url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(CallbackRequest.objects.filter(pk=req.pk).exists())


class CorporateRequestCRUDViewTests(TestCase):
    """Тесты CRUD корпоративных запросов."""

    def setUp(self):
        self.client = Client()
        self.user = create_staff_user('admin', role=StaffRole.ADMINISTRATOR)

    def test_list_and_create(self):
        self.client.login(username='admin', password='testpass123')
        list_url = reverse('admin_panel:corporaterequest_list')
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, 200)

        create_url = reverse('admin_panel:corporaterequest_create')
        data = {
            'organization_name': 'АО Тест',
            'contact_name': 'Контакт',
            'contact_position': 'HR',
            'phone': '+7 999 333-33-33',
            'email': 'hr@test.ru',
            'topics': 'Управление',
            'employees_count': 20,
            'desired_dates': 'осень 2026',
            'comment': '',
            'status': CorporateRequestStatus.NEW,
            'admin_comment': '',
        }
        response = self.client.post(create_url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(CorporateRequest.objects.count(), 1)


class StaffRoleAccessTests(TestCase):
    """Тесты ролей сотрудников."""

    def setUp(self):
        self.client = Client()
        self.admin = create_staff_user('administrator', role=StaffRole.ADMINISTRATOR)
        self.methodist = create_staff_user('methodist', role=StaffRole.METHODIST)
        self.editor = create_staff_user('editor', role=StaffRole.EDITOR)
        self.program = create_test_program()

    def test_editor_cannot_access_crm(self):
        self.client.login(username='editor', password='testpass123')
        response = self.client.get(reverse('admin_panel:application_list'))
        self.assertEqual(response.status_code, 403)

    def test_editor_can_access_content(self):
        self.client.login(username='editor', password='testpass123')
        response = self.client.get(reverse('admin_panel:publication_list'))
        self.assertEqual(response.status_code, 200)

    def test_methodist_can_access_crm_but_cannot_delete(self):
        application = Application.objects.create(
            full_name='Методист тест',
            program=self.program,
            email='m@example.com',
            phone='+7 999 000-00-01',
        )
        self.client.login(username='methodist', password='testpass123')
        list_response = self.client.get(reverse('admin_panel:application_list'))
        self.assertEqual(list_response.status_code, 200)

        delete_url = reverse('admin_panel:application_delete', args=[application.pk])
        delete_response = self.client.post(delete_url)
        self.assertEqual(delete_response.status_code, 403)
        self.assertTrue(Application.objects.filter(pk=application.pk).exists())

    def test_user_without_profile_denied(self):
        User.objects.create_user(username='noprofile', password='testpass123')
        self.client.login(username='noprofile', password='testpass123')
        response = self.client.get(reverse('admin_panel:dashboard'))
        self.assertEqual(response.status_code, 403)

    def test_superuser_without_profile_is_admin(self):
        User.objects.create_superuser(
            username='super',
            email='super@example.com',
            password='testpass123',
        )
        self.client.login(username='super', password='testpass123')
        response = self.client.get(reverse('admin_panel:application_list'))
        self.assertEqual(response.status_code, 200)


class AnalyticsServiceTests(TestCase):
    """Тесты агрегации аналитики."""

    def setUp(self):
        self.program = create_test_program()
        Application.objects.create(
            full_name='Заявка 1',
            program=self.program,
            email='a1@example.com',
            phone='+7 999 101-01-01',
            status=ApplicationStatus.NEW,
        )
        Application.objects.create(
            full_name='Заявка 2',
            program=self.program,
            email='a2@example.com',
            phone='+7 999 202-02-02',
            status=ApplicationStatus.CONFIRMED,
        )
        CorporateRequest.objects.create(
            organization_name='ООО А',
            contact_name='Контакт',
            phone='+7 999 303-03-03',
            email='corp@example.com',
            topics='Темы',
            employees_count=10,
            status=CorporateRequestStatus.QUOTE_SENT,
        )
        CallbackRequest.objects.create(
            name='Звонок',
            phone='+7 999 404-04-04',
            status=CallbackRequestStatus.NEW,
        )

    def test_build_analytics_crm_kpi(self):
        from admin_panel.analytics import build_analytics

        ctx = build_analytics(
            {'preset': '30'},
            include_crm=True,
            include_catalog=True,
            include_content=True,
        )
        self.assertEqual(ctx['crm_kpi']['apps_count'], 2)
        self.assertEqual(ctx['crm_kpi']['corps_count'], 1)
        self.assertEqual(ctx['crm_kpi']['calls_count'], 1)
        self.assertEqual(ctx['crm_kpi']['incoming'], 4)
        self.assertEqual(ctx['crm_kpi']['conversion_pct'], 50.0)
        self.assertEqual(ctx['crm_kpi']['quote_pct'], 100.0)
        self.assertEqual(ctx['crm_kpi']['backlog_new'], 2)  # 1 app + 1 callback
        self.assertIn('incoming_daily', ctx['chart_json'])
        self.assertIn('application_statuses', ctx['chart_json'])
        self.assertIn('top_programs', ctx['chart_json'])
        self.assertEqual(ctx['catalog_kpi']['active_programs'], 1)
        self.assertIn('program_statuses', ctx['chart_json'])
        self.assertIn('content_by_type', ctx['chart_json'])

    def test_build_analytics_without_crm(self):
        from admin_panel.analytics import build_analytics

        ctx = build_analytics(
            {},
            include_crm=False,
            include_catalog=False,
            include_content=True,
        )
        self.assertFalse(ctx['include_crm'])
        self.assertNotIn('crm_kpi', ctx)
        self.assertIn('content_kpi', ctx)


class AnalyticsViewTests(TestCase):
    """Тесты страницы аналитики и прав."""

    def setUp(self):
        self.client = Client()
        self.admin = create_staff_user('admin_a', role=StaffRole.ADMINISTRATOR)
        self.methodist = create_staff_user('methodist_a', role=StaffRole.METHODIST)
        self.editor = create_staff_user('editor_a', role=StaffRole.EDITOR)
        self.program = create_test_program()

    def test_analytics_requires_login(self):
        response = self.client.get(reverse('admin_panel:analytics'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_admin_sees_all_blocks(self):
        self.client.login(username='admin_a', password='testpass123')
        response = self.client.get(reverse('admin_panel:analytics'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['include_crm'])
        self.assertTrue(response.context['include_catalog'])
        self.assertTrue(response.context['include_content'])
        self.assertContains(response, 'Базовая аналитика')
        self.assertContains(response, 'chart-incoming-daily')

    def test_methodist_sees_crm(self):
        self.client.login(username='methodist_a', password='testpass123')
        response = self.client.get(reverse('admin_panel:analytics'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['include_crm'])
        self.assertContains(response, 'Обращения')

    def test_editor_sees_content_only(self):
        self.client.login(username='editor_a', password='testpass123')
        response = self.client.get(reverse('admin_panel:analytics'))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['include_crm'])
        self.assertFalse(response.context['include_catalog'])
        self.assertTrue(response.context['include_content'])
        self.assertNotContains(response, 'chart-incoming-daily')
        self.assertContains(response, 'Контент')
