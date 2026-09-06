from django.test import TestCase
from django.utils import timezone

from .choices import CallbackRequestStatus, CorporateRequestStatus
from .models import CallbackRequest, CorporateRequest, StaffProfile
from django.contrib.auth import get_user_model

User = get_user_model()


class CallbackRequestModelTests(TestCase):
    """Тесты модели CallbackRequest."""

    def test_callback_request_str_representation(self):
        """__str__ возвращает имя и телефон."""
        req = CallbackRequest.objects.create(
            name='Иван Иванов',
            phone='+7 999 123-45-67',
            email='ivan@example.com',
        )
        self.assertIn('Иван Иванов', str(req))
        self.assertIn('+7 999 123-45-67', str(req))

    def test_callback_request_created_at_auto_set(self):
        """created_at устанавливается автоматически при создании."""
        before = timezone.now()
        req = CallbackRequest.objects.create(
            name='Тест',
            phone='+7 999 000-00-00',
            email='test@example.com',
        )
        after = timezone.now()
        self.assertIsNotNone(req.created_at)
        self.assertGreaterEqual(req.created_at, before)
        self.assertLessEqual(req.created_at, after)

    def test_callback_request_default_status(self):
        req = CallbackRequest.objects.create(
            name='Статус',
            phone='+7 999 111-11-11',
        )
        self.assertEqual(req.status, CallbackRequestStatus.NEW)
        self.assertIsNotNone(req.updated_at)


class CorporateRequestModelTests(TestCase):
    def test_default_status(self):
        req = CorporateRequest.objects.create(
            organization_name='ООО Тест',
            contact_name='Контакт',
            phone='+7 999 222-22-22',
            email='corp@example.com',
            topics='Темы',
            employees_count=10,
        )
        self.assertEqual(req.status, CorporateRequestStatus.NEW)


class StaffProfileModelTests(TestCase):
    def test_str(self):
        user = User.objects.create_user(username='staff1', password='pass')
        profile = StaffProfile.objects.create(
            user=user,
            full_name='Сотрудник Один',
            role='methodist',
        )
        self.assertIn('Сотрудник Один', str(profile))
        self.assertIn('Методист', str(profile))
