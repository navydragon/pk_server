from datetime import date, timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from unittest.mock import patch

from core.choices import CourseBatchStatus, LearningFormatStatus, ProgramStatus, ProgramType
from core.models import Application, CallbackRequest, CourseBatch, Direction, LearningFormat, Program


class ActiveProgramsApiTests(APITestCase):
    def setUp(self):
        """Создаём тестовые данные"""
        self.direction = Direction.objects.create(
            name='Тестовое направление',
            status='active'
        )
        self.active_program = Program.objects.create(
            name='Активная программа',
            direction=self.direction,
            program_type=ProgramType.QUALIFICATION_UPGRADE,
            lead='Тестовый лид',
            about_description='Описание программы',
            curriculum='Учебный план',
            target_audience='Целевая аудитория',
            hours_volume=72,
            duration='2 месяца',
            cost='10000 руб',
            status=ProgramStatus.ACTIVE
        )
        self.draft_program = Program.objects.create(
            name='Черновик программы',
            direction=self.direction,
            program_type=ProgramType.QUALIFICATION_UPGRADE,
            lead='Тестовый лид',
            about_description='Описание программы',
            curriculum='Учебный план',
            target_audience='Целевая аудитория',
            hours_volume=72,
            duration='2 месяца',
            cost='10000 руб',
            status=ProgramStatus.DRAFT
        )

    def test_active_programs_endpoint_returns_200_and_list(self):
        """Проверяем, что эндпоинт возвращает список активных программ"""
        url = reverse('active-programs')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)

    def test_active_programs_endpoint_returns_only_active_programs(self):
        """Проверяем, что возвращаются только программы со статусом ACTIVE"""
        url = reverse('active-programs')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Проверяем, что активная программа есть в ответе
        program_names = [p['name'] for p in response.data]
        self.assertIn(self.active_program.name, program_names)
        
        # Проверяем, что черновик не попал в ответ
        self.assertNotIn(self.draft_program.name, program_names)

    def test_active_programs_endpoint_returns_correct_fields(self):
        """Проверяем, что в ответе есть все необходимые поля"""
        url = reverse('active-programs')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        if response.data:
            item = response.data[0]
            expected_fields = [
                'id', 'name', 'direction', 'direction_name', 'program_type', 'training_direction_code', 'lead',
                'about_description', 'curriculum', 'target_audience',
                'enrollment_process', 'learning_format', 'learning_format_comment', 'hours_volume',
                'duration', 'cost', 'outcome', 'requirements',
                'learning_outcomes', 'status', 'created_at', 'updated_at'
            ]
            for field in expected_fields:
                self.assertIn(field, item)


class ProgramsWithBatchesApiTests(APITestCase):
    def setUp(self):
        """Создаём тестовые данные"""
        self.direction = Direction.objects.create(
            name='Тестовое направление',
            status='active'
        )
        self.learning_format = LearningFormat.objects.create(
            name='Очная',
            status=LearningFormatStatus.ACTIVE
        )
        self.program = Program.objects.create(
            name='Тестовая программа',
            direction=self.direction,
            program_type=ProgramType.QUALIFICATION_UPGRADE,
            lead='Тестовый лид',
            about_description='Описание программы',
            curriculum='Учебный план',
            target_audience='Целевая аудитория',
            hours_volume=72,
            duration='2 месяца',
            cost='10000 руб',
            status=ProgramStatus.ACTIVE,
            learning_format=self.learning_format
        )
        # Поток с будущей датой
        self.future_batch = CourseBatch.objects.create(
            program=self.program,
            start_date=date.today() + timedelta(days=30),
            end_date=date.today() + timedelta(days=60),
            learning_format=self.learning_format,
            cost='15000 руб',
            status=CourseBatchStatus.ENROLLMENT_OPEN
        )
        # Поток с прошедшей датой (не должен попасть в ответ)
        self.past_batch = CourseBatch.objects.create(
            program=self.program,
            start_date=date.today() - timedelta(days=30),
            end_date=date.today() - timedelta(days=10),
            learning_format=self.learning_format,
            cost='10000 руб',
            status=CourseBatchStatus.COMPLETED
        )

    def test_programs_with_batches_endpoint_returns_200(self):
        """Проверяем, что эндпоинт возвращает 200"""
        url = reverse('programs-with-batches')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)

    def test_programs_with_batches_filters_by_date(self):
        """Проверяем, что возвращаются только потоки с датой начала >= текущей даты"""
        url = reverse('programs-with-batches')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        if response.data:
            program = response.data[0]
            self.assertIn('batches', program)
            batches = program['batches']
            
            # Проверяем, что есть только будущие потоки
            for batch in batches:
                batch_date = date.fromisoformat(batch['start_date'])
                self.assertGreaterEqual(batch_date, date.today())
            
            # Проверяем, что прошедший поток не попал в ответ
            batch_ids = [b['id'] for b in batches]
            self.assertIn(self.future_batch.id, batch_ids)
            self.assertNotIn(self.past_batch.id, batch_ids)

    def test_programs_without_batches_excluded(self):
        """Проверяем, что программы без подходящих потоков исключаются"""
        # Создаем программу без потоков
        program_no_batches = Program.objects.create(
            name='Программа без потоков',
            direction=self.direction,
            program_type=ProgramType.QUALIFICATION_UPGRADE,
            lead='Тестовый лид',
            about_description='Описание',
            curriculum='План',
            target_audience='Аудитория',
            hours_volume=72,
            duration='2 месяца',
            cost='10000 руб',
            status=ProgramStatus.ACTIVE,
            learning_format=self.learning_format
        )

        url = reverse('programs-with-batches')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        program_names = [p['name'] for p in response.data]
        self.assertNotIn(program_no_batches.name, program_names)

    def test_programs_with_batches_correct_structure(self):
        """Проверяем корректность структуры ответа"""
        url = reverse('programs-with-batches')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        if response.data:
            program = response.data[0]
            expected_program_fields = ['id', 'name', 'direction_name', 'learning_format', 'hours_volume', 'batches']
            for field in expected_program_fields:
                self.assertIn(field, program)

            if program['batches']:
                batch = program['batches'][0]
                expected_batch_fields = [
                    'id', 'start_date', 'end_date', 'learning_format', 'cost', 'status',
                    'enrollment_status_text', 'action_button_text', 'is_action_enabled'
                ]
                for field in expected_batch_fields:
                    self.assertIn(field, batch)

    def test_batch_status_mapping(self):
        """Проверяем маппинг статусов потоков"""
        # Создаем потоки с разными статусами
        batch_open = CourseBatch.objects.create(
            program=self.program,
            start_date=date.today() + timedelta(days=10),
            learning_format=self.learning_format,
            cost='15000 руб',
            status=CourseBatchStatus.ENROLLMENT_OPEN
        )
        batch_closed = CourseBatch.objects.create(
            program=self.program,
            start_date=date.today() + timedelta(days=20),
            learning_format=self.learning_format,
            cost='20000 руб',
            status=CourseBatchStatus.ENROLLMENT_CLOSED
        )
        batch_completed = CourseBatch.objects.create(
            program=self.program,
            start_date=date.today() + timedelta(days=30),
            learning_format=self.learning_format,
            cost='25000 руб',
            status=CourseBatchStatus.COMPLETED
        )

        url = reverse('programs-with-batches')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        if response.data:
            program = response.data[0]
            batches_dict = {b['id']: b for b in program['batches']}
            
            # Проверяем статус enrollment_open
            if batch_open.id in batches_dict:
                batch = batches_dict[batch_open.id]
                self.assertEqual(batch['enrollment_status_text'], 'Открыта запись')
                self.assertEqual(batch['action_button_text'], 'Записаться')
                self.assertTrue(batch['is_action_enabled'])
            
            # Проверяем статус enrollment_closed
            if batch_closed.id in batches_dict:
                batch = batches_dict[batch_closed.id]
                self.assertEqual(batch['enrollment_status_text'], 'Запись закрыта')
                self.assertEqual(batch['action_button_text'], 'Запись закрыта')
                self.assertFalse(batch['is_action_enabled'])
            
            # Проверяем статус completed
            if batch_completed.id in batches_dict:
                batch = batches_dict[batch_completed.id]
                self.assertEqual(batch['enrollment_status_text'], 'Набор завершен')
                self.assertEqual(batch['action_button_text'], 'Набор завершен')
                self.assertFalse(batch['is_action_enabled'])


class ProgramDetailApiTests(APITestCase):
    def setUp(self):
        """Создаём программу с формой обучения для детального просмотра."""
        self.direction = Direction.objects.create(
            name='Направление для ProgramDetail',
            status='active'
        )
        self.learning_format = LearningFormat.objects.create(
            name='Очная формальная',
            status=LearningFormatStatus.ACTIVE
        )
        self.program = Program.objects.create(
            name='Программа с формой обучения',
            direction=self.direction,
            program_type=ProgramType.QUALIFICATION_UPGRADE,
            lead='Лид',
            about_description='Описание',
            curriculum='План',
            target_audience='Аудитория',
            hours_volume=72,
            duration='2 месяца',
            cost='10000 руб',
            status=ProgramStatus.ACTIVE,
            learning_format=self.learning_format,
        )

    def test_program_detail_has_simple_learning_format(self):
        """Детальный эндпоинт возвращает строковое поле learning_format."""
        url = reverse('program-detail', args=[self.program.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertIn('learning_format', data)
        self.assertEqual(data['learning_format'], self.learning_format.name)


class ApplicationCreateApiTests(APITestCase):
    """Тесты API создания заявки."""

    def setUp(self):
        self.direction = Direction.objects.create(
            name='Тестовое направление API',
            status='active'
        )
        self.learning_format = LearningFormat.objects.create(
            name='Очная API',
            status=LearningFormatStatus.ACTIVE
        )
        self.program = Program.objects.create(
            name='Тестовая программа API',
            direction=self.direction,
            program_type=ProgramType.QUALIFICATION_UPGRADE,
            lead='Лид',
            about_description='Описание',
            curriculum='План',
            target_audience='Аудитория',
            hours_volume=72,
            duration='2 месяца',
            cost='10000 руб',
            status=ProgramStatus.ACTIVE,
            learning_format=self.learning_format
        )
        self.batch = CourseBatch.objects.create(
            program=self.program,
            learning_format=self.learning_format,
            start_date='2025-06-01',
            status=CourseBatchStatus.ENROLLMENT_OPEN
        )

    @patch('emails.services.send_mail')
    def test_application_create_returns_201(self, mock_send_mail):
        """Создание заявки возвращает 201 и создаёт запись."""
        url = reverse('application-create')
        data = {
            'full_name': 'API Тестовый Слушатель',
            'program': self.program.id,
            'email': 'api-test@example.com',
            'phone': '+7 999 000-00-00',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Application.objects.count(), 1)
        app = Application.objects.first()
        self.assertEqual(app.full_name, 'API Тестовый Слушатель')
        self.assertEqual(app.email, 'api-test@example.com')
        self.assertIn('id', response.data)
        self.assertIn('created_at', response.data)

    @patch('emails.services.send_mail')
    def test_application_create_sends_email(self, mock_send_mail):
        """При создании заявки отправляется email-уведомление."""
        url = reverse('application-create')
        data = {
            'full_name': 'Email Test',
            'program': self.program.id,
            'email': 'email-test@example.com',
            'phone': '+7 999 111-11-11',
        }
        self.client.post(url, data, format='json')
        mock_send_mail.assert_called_once()


class CallbackRequestCreateApiTests(APITestCase):
    """Тесты API создания запроса обратного звонка."""

    @patch('emails.services.send_mail')
    def test_callback_request_create_returns_201(self, mock_send_mail):
        """Создание запроса возвращает 201 и создаёт запись."""
        url = reverse('callback-request-create')
        data = {
            'name': 'Иван Иванов',
            'phone': '+7 999 123-45-67',
            'email': 'ivan@example.com',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CallbackRequest.objects.count(), 1)
        req = CallbackRequest.objects.first()
        self.assertEqual(req.name, 'Иван Иванов')
        self.assertEqual(req.phone, '+7 999 123-45-67')
        self.assertEqual(req.email, 'ivan@example.com')
        self.assertIn('id', response.data)
        self.assertIn('created_at', response.data)

    @patch('emails.services.send_mail')
    def test_callback_request_create_returns_correct_fields(self, mock_send_mail):
        """Ответ содержит все ожидаемые поля."""
        url = reverse('callback-request-create')
        data = {
            'name': 'Петр Петров',
            'phone': '+7 999 000-00-00',
            'email': 'petr@example.com',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        expected_fields = ['id', 'name', 'phone', 'email', 'created_at']
        for field in expected_fields:
            self.assertIn(field, response.data)

    @patch('emails.services.send_mail')
    def test_callback_request_create_sends_email(self, mock_send_mail):
        """При создании запроса отправляется email-уведомление."""
        url = reverse('callback-request-create')
        data = {
            'name': 'Email Test',
            'phone': '+7 999 111-11-11',
            'email': 'callback-test@example.com',
        }
        self.client.post(url, data, format='json')
        mock_send_mail.assert_called_once()

    def test_callback_request_create_validation_error_missing_fields(self):
        """Ошибка валидации при отсутствии обязательных полей."""
        url = reverse('callback-request-create')
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(CallbackRequest.objects.count(), 0)

    def test_callback_request_create_validation_error_invalid_email(self):
        """Ошибка валидации при неверном формате email."""
        url = reverse('callback-request-create')
        data = {
            'name': 'Тест',
            'phone': '+7 999 000-00-00',
            'email': 'invalid-email',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(CallbackRequest.objects.count(), 0)

