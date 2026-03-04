from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from core.choices import ApplicationStatus, CourseBatchStatus, LearningFormatStatus, ProgramStatus, ProgramType
from core.models import Application, CallbackRequest, CourseBatch, Direction, LearningFormat, Program

User = get_user_model()


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
        """Проверка строкового представления заявки."""
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
        """Проверка, что статус по умолчанию — новая."""
        program = create_test_program()
        application = Application.objects.create(
            full_name='Петров Пётр',
            program=program,
            email='petrov@example.com',
            phone='+7 999 111-22-33'
        )
        self.assertEqual(application.status, ApplicationStatus.NEW)

    def test_application_created_at_auto_set(self):
        """Проверка, что дата создания устанавливается автоматически."""
        program = create_test_program()
        application = Application.objects.create(
            full_name='Сидоров Сидор',
            program=program,
            email='sidorov@example.com',
            phone='+7 999 444-55-66'
        )
        self.assertIsNotNone(application.created_at)


class ApplicationCRUDViewTests(TestCase):
    """Тесты CRUD представлений для заявок."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='admin',
            password='testpass123'
        )
        self.program = create_test_program()
        self.batch = create_test_batch(self.program)

    def test_application_list_requires_login(self):
        """Список заявок требует авторизации."""
        url = reverse('admin_panel:application_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_application_list_renders_for_authenticated_user(self):
        """Список заявок отображается для авторизованного пользователя."""
        self.client.login(username='admin', password='testpass123')
        url = reverse('admin_panel:application_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('applications', response.context)

    def test_application_create_success(self):
        """Успешное создание заявки."""
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
        }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Application.objects.count(), 1)
        app = Application.objects.first()
        self.assertEqual(app.full_name, 'Новый Слушатель')
        self.assertEqual(app.email, 'new@example.com')

    def test_application_update_success(self):
        """Успешное обновление заявки."""
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
        }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        application.refresh_from_db()
        self.assertEqual(application.full_name, 'Обновлённое Имя')
        self.assertEqual(application.status, ApplicationStatus.IN_PROGRESS)

    def test_application_delete_success(self):
        """Успешное удаление заявки."""
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


class ApplicationFormTests(TestCase):
    """Тесты формы заявки."""

    def setUp(self):
        self.program = create_test_program('Направление 1')
        self.batch = create_test_batch(self.program)
        self.other_program = create_test_program('Направление 2')
        self.other_batch = create_test_batch(self.other_program, format_name='Онлайн')

    def test_application_form_valid_data(self):
        """Форма валидна при корректных данных."""
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
        }
        form = ApplicationForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_application_form_batch_must_belong_to_program(self):
        """Поток должен относиться к выбранной программе."""
        from admin_panel.forms import ApplicationForm

        data = {
            'full_name': 'Невалидный Выбор',
            'program': self.program.pk,
            'batch': self.other_batch.pk,  # поток от другой программы
            'email': 'invalid@example.com',
            'phone': '+7 999 666-66-66',
            'status': ApplicationStatus.NEW,
            'comment': '',
            'admin_comment': '',
        }
        form = ApplicationForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('batch', form.errors)


class CallbackRequestCRUDViewTests(TestCase):
    """Тесты CRUD представлений для запросов обратного звонка."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='admin',
            password='testpass123'
        )

    def test_callbackrequest_list_requires_login(self):
        """Список запросов обратного звонка требует авторизации."""
        url = reverse('admin_panel:callbackrequest_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_callbackrequest_list_renders_for_authenticated_user(self):
        """Список запросов отображается для авторизованного пользователя."""
        self.client.login(username='admin', password='testpass123')
        url = reverse('admin_panel:callbackrequest_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('callback_requests', response.context)

    def test_callbackrequest_create_success(self):
        """Успешное создание запроса обратного звонка."""
        self.client.login(username='admin', password='testpass123')
        url = reverse('admin_panel:callbackrequest_create')
        data = {
            'name': 'Иван Иванов',
            'phone': '+7 999 123-45-67',
            'email': 'ivan@example.com',
        }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(CallbackRequest.objects.count(), 1)
        req = CallbackRequest.objects.first()
        self.assertEqual(req.name, 'Иван Иванов')
        self.assertEqual(req.email, 'ivan@example.com')

    def test_callbackrequest_update_success(self):
        """Успешное обновление запроса обратного звонка."""
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
        }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        req.refresh_from_db()
        self.assertEqual(req.name, 'Обновлённое Имя')
        self.assertEqual(req.email, 'updated@example.com')

    def test_callbackrequest_delete_success(self):
        """Успешное удаление запроса обратного звонка."""
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
