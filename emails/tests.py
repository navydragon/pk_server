"""Тесты приложения emails."""

from unittest.mock import patch

from django.conf import settings
from django.test import TestCase, override_settings

from core.choices import ApplicationStatus, CourseBatchStatus, LearningFormatStatus, ProgramStatus, ProgramType
from core.models import Application, CallbackRequest, CourseBatch, Direction, LearningFormat, Program

from .services import send_application_notification, send_callback_request_notification


def create_test_application():
    """Создаёт тестовую заявку."""
    direction = Direction.objects.create(
        name='Направление для emails',
        status='active'
    )
    learning_format = LearningFormat.objects.create(
        name='Очная emails',
        status=LearningFormatStatus.ACTIVE
    )
    program = Program.objects.create(
        name='Программа для emails',
        direction=direction,
        program_type=ProgramType.QUALIFICATION_UPGRADE,
        lead='Лид',
        about_description='Описание',
        curriculum='План',
        target_audience='Аудитория',
        hours_volume=72,
        duration='2 месяца',
        cost='10000 руб',
        status=ProgramStatus.ACTIVE,
        learning_format=learning_format
    )
    batch = CourseBatch.objects.create(
        program=program,
        learning_format=learning_format,
        start_date='2025-07-01',
        status=CourseBatchStatus.ENROLLMENT_OPEN
    )
    return Application.objects.create(
        full_name='Тестовый Слушатель',
        program=program,
        batch=batch,
        email='test@example.com',
        phone='+7 999 222-33-44',
        comment='Тестовый комментарий',
    )


@override_settings(NOTIFICATION_EMAIL='admin@test.ru')
class SendApplicationNotificationTests(TestCase):
    """Тесты send_application_notification."""

    @patch('emails.services.send_mail')
    def test_send_application_notification_calls_send_mail(self, mock_send_mail):
        """send_application_notification вызывает send_mail с правильными аргументами."""
        application = create_test_application()

        result = send_application_notification(application)

        mock_send_mail.assert_called_once()
        call_args = mock_send_mail.call_args
        self.assertEqual(call_args.kwargs['recipient_list'], ['admin@test.ru'])
        self.assertIn(application.full_name, call_args.kwargs['subject'])
        self.assertIn(application.program.name, call_args.kwargs['subject'])
        self.assertIn(application.full_name, call_args.kwargs['message'])
        self.assertIn(application.email, call_args.kwargs['message'])
        self.assertIn(application.phone, call_args.kwargs['message'])
        self.assertEqual(result, mock_send_mail.return_value)

    @override_settings(NOTIFICATION_EMAIL='')
    @patch('emails.services.send_mail')
    def test_send_application_notification_skips_when_no_recipient(self, mock_send_mail):
        """Не отправляет письмо, если NOTIFICATION_EMAIL не задан."""
        application = create_test_application()

        result = send_application_notification(application)

        mock_send_mail.assert_not_called()
        self.assertEqual(result, 0)


def create_test_callback_request():
    """Создаёт тестовый запрос обратного звонка."""
    return CallbackRequest.objects.create(
        name='Тестовый Клиент',
        phone='+7 999 555-66-77',
        email='callback@example.com',
    )


@override_settings(NOTIFICATION_EMAIL='admin@test.ru')
class SendCallbackRequestNotificationTests(TestCase):
    """Тесты send_callback_request_notification."""

    @patch('emails.services.send_mail')
    def test_send_callback_request_notification_calls_send_mail(self, mock_send_mail):
        """send_callback_request_notification вызывает send_mail с правильными аргументами."""
        callback_request = create_test_callback_request()

        result = send_callback_request_notification(callback_request)

        mock_send_mail.assert_called_once()
        call_args = mock_send_mail.call_args
        self.assertEqual(call_args.kwargs['recipient_list'], ['admin@test.ru'])
        self.assertIn(callback_request.name, call_args.kwargs['subject'])
        self.assertIn('обратного звонка', call_args.kwargs['subject'])
        self.assertIn(callback_request.name, call_args.kwargs['message'])
        self.assertIn(callback_request.email, call_args.kwargs['message'])
        self.assertIn(callback_request.phone, call_args.kwargs['message'])
        self.assertEqual(result, mock_send_mail.return_value)

    @override_settings(NOTIFICATION_EMAIL='')
    @patch('emails.services.send_mail')
    def test_send_callback_request_notification_skips_when_no_recipient(self, mock_send_mail):
        """Не отправляет письмо, если NOTIFICATION_EMAIL не задан."""
        callback_request = create_test_callback_request()

        result = send_callback_request_notification(callback_request)

        mock_send_mail.assert_not_called()
        self.assertEqual(result, 0)
