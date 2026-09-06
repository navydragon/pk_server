from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from unittest.mock import patch

from core.choices import (
    DirectionStatus,
    LearningFormatStatus,
    ProgramStatus,
    ProgramType,
)
from core.models import Direction, LearningFormat, Program

from advisor.catalog import get_program, get_quiz_filters, search_programs


class AdvisorCatalogTests(TestCase):
    def setUp(self):
        self.direction = Direction.objects.create(
            name='Программирование и IT',
            status=DirectionStatus.ACTIVE,
        )
        self.format_online = LearningFormat.objects.create(
            name='Онлайн с преподавателем',
            status=LearningFormatStatus.ACTIVE,
        )
        self.format_offline = LearningFormat.objects.create(
            name='Очный',
            status=LearningFormatStatus.ACTIVE,
        )
        self.python = Program.objects.create(
            name='Python для начинающих',
            direction=self.direction,
            program_type=ProgramType.QUALIFICATION_UPGRADE,
            lead='Python с нуля',
            about_description='Описание Python',
            curriculum='План',
            target_audience='Начинающие разработчики',
            learning_format=self.format_online,
            hours_volume=72,
            duration='2 месяца',
            cost='35000',
            status=ProgramStatus.ACTIVE,
            position=1,
        )
        self.ba = Program.objects.create(
            name='Бизнес-анализ с нуля',
            direction=Direction.objects.create(
                name='Бизнес-анализ',
                status=DirectionStatus.ACTIVE,
            ),
            program_type=ProgramType.QUALIFICATION_UPGRADE,
            lead='BA intro',
            about_description='Описание BA',
            curriculum='План',
            target_audience='Начинающие аналитики',
            learning_format=self.format_offline,
            hours_volume=48,
            duration='1 месяц',
            cost='28000',
            status=ProgramStatus.ACTIVE,
            position=2,
        )
        Program.objects.create(
            name='Черновик курса',
            direction=self.direction,
            program_type=ProgramType.QUALIFICATION_UPGRADE,
            lead='draft',
            about_description='draft',
            curriculum='draft',
            target_audience='draft',
            learning_format=self.format_online,
            hours_volume=40,
            duration='1 месяц',
            cost='10000',
            status=ProgramStatus.DRAFT,
            position=99,
        )

    def test_search_by_query(self):
        result = search_programs(query='Python')
        names = [item['name'] for item in result]
        self.assertIn('Python для начинающих', names)
        self.assertNotIn('Черновик курса', names)

    def test_search_by_format_and_cost(self):
        result = search_programs(learning_format='Очный', max_cost=30000)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], 'Бизнес-анализ с нуля')

    def test_get_program_active_only(self):
        self.assertIsNotNone(get_program(self.python.id))
        draft = Program.objects.get(name='Черновик курса')
        self.assertIsNone(get_program(draft.id))

    def test_quiz_filters(self):
        data = get_quiz_filters()
        self.assertTrue(any(d['name'] == 'Программирование и IT' for d in data['directions']))
        self.assertTrue(any(f['name'] == 'Очный' for f in data['formats']))
        self.assertEqual(len(data['program_types']), 2)


class AdvisorApiTests(APITestCase):
    def setUp(self):
        direction = Direction.objects.create(
            name='Программирование и IT',
            status=DirectionStatus.ACTIVE,
        )
        fmt = LearningFormat.objects.create(
            name='Онлайн с преподавателем',
            status=LearningFormatStatus.ACTIVE,
        )
        self.program = Program.objects.create(
            name='Python для начинающих',
            direction=direction,
            program_type=ProgramType.QUALIFICATION_UPGRADE,
            lead='Python с нуля',
            about_description='Описание',
            curriculum='План',
            target_audience='Начинающие',
            learning_format=fmt,
            hours_volume=72,
            duration='2 месяца',
            cost='35000',
            status=ProgramStatus.ACTIVE,
        )

    def test_filters_endpoint(self):
        url = reverse('advisor-filters')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('directions', response.data)
        self.assertIn('formats', response.data)

    def test_chat_without_llm_returns_503(self):
        url = reverse('advisor-chat')
        with self.settings(LLM_API_KEY='', LLM_MODEL=''):
            response = self.client.post(
                url,
                {'message': 'Нужен Python'},
                format='json',
            )
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)

    @patch('advisor.views.run_advisor_chat')
    def test_chat_with_mock_agent(self, mocked_run):
        async def fake_run(*, message, history):
            return (
                f'Рекомендую программу id={self.program.id}',
                [self.program.id],
            )

        mocked_run.side_effect = fake_run
        url = reverse('advisor-chat')
        with self.settings(LLM_API_KEY='test-key', LLM_MODEL='test-model'):
            response = self.client.post(
                url,
                {
                    'message': 'Нужен Python с нуля',
                    'history': [],
                },
                format='json',
            )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(str(self.program.id), response.data['reply'])
        self.assertEqual(len(response.data['programs']), 1)
        self.assertEqual(response.data['programs'][0]['id'], self.program.id)
        self.assertEqual(response.data['programs'][0]['name'], self.program.name)
        mocked_run.assert_called_once()
