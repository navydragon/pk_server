from django.test import TestCase
from django.utils import timezone

from .models import CallbackRequest


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
