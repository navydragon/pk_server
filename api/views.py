import uuid
import uuid
from datetime import date

from django.db.models import Prefetch
from django.http import Http404
from django.utils.text import slugify
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED
from rest_framework.views import APIView

from core.choices import ProgramStatus
from core.models import Application, CallbackRequest, CourseBatch, Program
from publications.choices import PublicationStatus, PublicationType
from publications.models import Case, Publication, Testimonial

from .serializers import (
    ApplicationCreateSerializer,
    CallbackRequestCreateSerializer,
    ProgramDetailSerializer,
    ProgramSerializer,
    ProgramWithBatchesSerializer,
    PublicationDetailSerializer,
    PublicationListSerializer,
    CaseDetailSerializer,
    CaseListSerializer,
    TestimonialCreateResponseSerializer,
    TestimonialCreateSerializer,
    TestimonialDetailSerializer,
    TestimonialListSerializer,
)


class ActiveProgramsView(APIView):
    """
    Возвращает список активных программ повышения квалификации.

    Эндпоинт открыт: не использует аутентификацию и авторизацию.
    """

    authentication_classes: list = []
    permission_classes: list = []
    # Ограничиваем рендереры только JSON, чтобы в Swagger не было выбора content type
    renderer_classes = [JSONRenderer]

    @extend_schema(
        summary='Список активных программ',
        description='Возвращает список всех активных программ повышения квалификации со статусом "active".',
        responses={200: ProgramSerializer(many=True)},
        tags=['Программы'],
    )
    def get(self, request, *args, **kwargs):
        programs = Program.objects.filter(status=ProgramStatus.ACTIVE).select_related('direction', 'learning_format').order_by('position', 'name')
        serializer = ProgramSerializer(programs, many=True)
        return Response(serializer.data)


class ProgramsWithBatchesView(APIView):
    """
    Возвращает список активных программ с потоками, у которых дата начала >= текущей даты.

    Эндпоинт открыт: не использует аутентификацию и авторизацию.
    """

    authentication_classes: list = []
    permission_classes: list = []
    renderer_classes = [JSONRenderer]

    @extend_schema(
        summary='Список программ с потоками',
        description='Возвращает список активных программ с потоками, у которых дата начала >= текущей даты. '
                    'Программы без подходящих потоков исключаются из ответа.',
        responses={200: ProgramWithBatchesSerializer(many=True)},
        tags=['Потоки'],
    )
    def get(self, request, *args, **kwargs):
        # Получаем текущую дату (используем date.today() для сравнения с DateField)
        current_date = date.today()

        # Создаем Prefetch для потоков с фильтрацией по дате и оптимизацией
        batches_prefetch = Prefetch(
            'batches',
            queryset=CourseBatch.objects.filter(
                start_date__gte=current_date
            ).select_related('learning_format').order_by('start_date')
        )

        # Получаем все активные программы с оптимизированными запросами
        programs = Program.objects.filter(
            status=ProgramStatus.ACTIVE
        ).select_related(
            'direction'
        ).prefetch_related(
            batches_prefetch
        ).order_by('position', 'name')

        # Фильтруем программы, у которых есть потоки после фильтрации по дате
        programs_with_batches = [
            program for program in programs
            if program.batches.exists()
        ]

        serializer = ProgramWithBatchesSerializer(programs_with_batches, many=True)
        return Response(serializer.data)


class ProgramDetailView(APIView):
    """
    Возвращает детальную информацию о программе по ID с текущими и будущими потоками.

    Эндпоинт открыт: не использует аутентификацию и авторизацию.
    """

    authentication_classes: list = []
    permission_classes: list = []
    renderer_classes = [JSONRenderer]

    @extend_schema(
        summary='Детальная информация о программе',
        description='''
        Возвращает полную информацию о программе повышения квалификации по её идентификатору.
        
        **Особенности:**
        - Возвращает все поля программы (название, описание, стоимость, требования и т.д.)
        - Включает список текущих и будущих потоков (дата начала >= текущей даты)
        - Потоки отсортированы по дате начала (от ближайших к дальним)
        - Для каждого потока возвращается информация о статусе записи и доступности действий
        
        **Фильтрация потоков:**
        - В ответ включаются только потоки с датой начала >= текущей даты
        - Прошедшие потоки не возвращаются
        
        **Ошибки:**
        - 404: Программа с указанным ID не найдена
        
        **Пример использования:**
        ```
        GET /api/programs/1/
        ```
        ''',
        parameters=[
            OpenApiParameter(
                name='program_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='Идентификатор программы (целое число)',
                required=True,
            ),
        ],
        responses={
            200: ProgramDetailSerializer,
            404: OpenApiResponse(description='Программа не найдена'),
        },
        tags=['Программы'],
    )
    def get(self, request, program_id, *args, **kwargs):
        # Получаем текущую дату для фильтрации потоков
        current_date = date.today()

        # Создаем Prefetch для потоков с фильтрацией по дате и оптимизацией
        batches_prefetch = Prefetch(
            'batches',
            queryset=CourseBatch.objects.filter(
                start_date__gte=current_date
            ).select_related('learning_format').order_by('start_date')
        )

        try:
            # Получаем программу с оптимизированными запросами
            # Используем select_related для direction и learning_format (ForeignKey)
            # Используем prefetch_related для batches (обратная связь)
            program = Program.objects.select_related(
                'direction',
                'learning_format'
            ).prefetch_related(
                batches_prefetch
            ).get(id=program_id)
        except Program.DoesNotExist:
            raise Http404('Программа не найдена')

        serializer = ProgramDetailSerializer(program)
        return Response(serializer.data)


def _send_application_notification(application):
    """Импорт и вызов отправки уведомления (избегаем циклических импортов)."""
    from emails.services import send_application_notification
    send_application_notification(application)


def _send_callback_request_notification(callback_request):
    """Импорт и вызов отправки уведомления о запросе обратного звонка."""
    from emails.services import send_callback_request_notification
    send_callback_request_notification(callback_request)


class ApplicationCreateView(APIView):
    """
    Создание заявки слушателя на обучение.

    Эндпоинт открыт: не использует аутентификацию.
    При успешном создании отправляется email-уведомление на NOTIFICATION_EMAIL.
    """

    authentication_classes: list = []
    permission_classes: list = []
    renderer_classes = [JSONRenderer]

    @extend_schema(
        summary='Создать заявку',
        description='Создаёт заявку слушателя на обучение. '
                    'Поле batch (поток) необязательно. '
                    'При успешном создании отправляется уведомление на email администратора.',
        request=ApplicationCreateSerializer,
        responses={
            201: ApplicationCreateSerializer,
            400: OpenApiResponse(description='Ошибки валидации'),
        },
        tags=['Заявки'],
    )
    def post(self, request, *args, **kwargs):
        serializer = ApplicationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        application = serializer.save()
        _send_application_notification(application)
        return Response(serializer.data, status=HTTP_201_CREATED)


class CallbackRequestCreateView(APIView):
    """
    Создание запроса на обратный звонок.

    Эндпоинт открыт: не использует аутентификацию.
    При успешном создании отправляется email-уведомление на NOTIFICATION_EMAIL.
    """

    authentication_classes: list = []
    permission_classes: list = []
    renderer_classes = [JSONRenderer]

    @extend_schema(
        summary='Создать запрос обратного звонка',
        description='Создаёт запрос на обратный звонок. '
                    'При успешном создании отправляется уведомление на email администратора.',
        request=CallbackRequestCreateSerializer,
        responses={
            201: CallbackRequestCreateSerializer,
            400: OpenApiResponse(description='Ошибки валидации'),
        },
        tags=['Обратный звонок'],
    )
    def post(self, request, *args, **kwargs):
        serializer = CallbackRequestCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        callback_request = serializer.save()
        _send_callback_request_notification(callback_request)
        return Response(serializer.data, status=HTTP_201_CREATED)


# --- Publications / Cases / Testimonials API ---

def _get_publication_queryset():
    """Базовый queryset только для опубликованных новостей и статей."""
    return Publication.objects.filter(
        status=PublicationStatus.PUBLISHED
    ).prefetch_related('categories', 'tags')


class PublicationListView(APIView):
    """Список публикаций (новости/статьи). Только опубликованные."""

    authentication_classes: list = []
    permission_classes: list = []
    renderer_classes = [JSONRenderer]

    @extend_schema(
        summary='Список публикаций',
        description='Список новостей и статей со статусом "Опубликовано".',
        parameters=[
            OpenApiParameter('type', str, description='Фильтр по типу: news, article'),
            OpenApiParameter('featured', bool, description='Только избранные'),
            OpenApiParameter('limit', int, description='Лимит записей'),
            OpenApiParameter('offset', int, description='Смещение'),
        ],
        responses={200: PublicationListSerializer(many=True)},
        tags=['Публикации'],
    )
    def get(self, request):
        qs = _get_publication_queryset()
        if request.query_params.get('featured') == 'true':
            qs = qs.filter(is_featured=True)
        if request.query_params.get('type'):
            qs = qs.filter(type=request.query_params['type'])
        limit = request.query_params.get('limit', 50)
        offset = int(request.query_params.get('offset', 0))
        qs = qs[offset:offset + int(limit)]
        serializer = PublicationListSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)


class PublicationFeaturedView(APIView):
    """Избранные публикации для главной."""

    authentication_classes: list = []
    permission_classes: list = []
    renderer_classes = [JSONRenderer]

    @extend_schema(
        summary='Избранные публикации',
        responses={200: PublicationListSerializer(many=True)},
        tags=['Публикации'],
    )
    def get(self, request):
        qs = _get_publication_queryset().filter(is_featured=True)[:10]
        serializer = PublicationListSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)


class PublicationDetailView(APIView):
    """Детальная публикация по slug."""

    authentication_classes: list = []
    permission_classes: list = []
    renderer_classes = [JSONRenderer]

    @extend_schema(
        summary='Детальная публикация',
        responses={200: PublicationDetailSerializer, 404: OpenApiResponse(description='Не найдено')},
        tags=['Публикации'],
    )
    def get(self, request, slug):
        try:
            pub = _get_publication_queryset().get(slug=slug)
        except Publication.DoesNotExist:
            raise Http404('Публикация не найдена')
        serializer = PublicationDetailSerializer(pub, context={'request': request})
        return Response(serializer.data)


class CaseListView(APIView):
    """Список кейсов."""

    authentication_classes: list = []
    permission_classes: list = []
    renderer_classes = [JSONRenderer]

    @extend_schema(
        summary='Список кейсов',
        parameters=[
            OpenApiParameter('featured', bool),
            OpenApiParameter('limit', int),
            OpenApiParameter('offset', int),
        ],
        responses={200: CaseListSerializer(many=True)},
        tags=['Кейсы'],
    )
    def get(self, request):
        qs = Case.objects.filter(status=PublicationStatus.PUBLISHED)
        if request.query_params.get('featured') == 'true':
            qs = qs.filter(is_featured=True)
        limit = int(request.query_params.get('limit', 50))
        offset = int(request.query_params.get('offset', 0))
        qs = qs[offset:offset + limit]
        serializer = CaseListSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)


class CaseDetailView(APIView):
    """Детальный кейс по slug."""

    authentication_classes: list = []
    permission_classes: list = []
    renderer_classes = [JSONRenderer]

    @extend_schema(
        summary='Детальный кейс',
        responses={200: CaseDetailSerializer, 404: OpenApiResponse(description='Не найдено')},
        tags=['Кейсы'],
    )
    def get(self, request, slug):
        try:
            case = Case.objects.filter(status=PublicationStatus.PUBLISHED).get(slug=slug)
        except Case.DoesNotExist:
            raise Http404('Кейс не найден')
        serializer = CaseDetailSerializer(case, context={'request': request})
        return Response(serializer.data)


class TestimonialListCreateView(APIView):
    """Список отзывов (GET) и создание отзыва (POST)."""

    authentication_classes: list = []
    permission_classes: list = []
    renderer_classes = [JSONRenderer]

    @extend_schema(
        summary='Список отзывов',
        parameters=[
            OpenApiParameter('featured', bool),
            OpenApiParameter('limit', int),
            OpenApiParameter('offset', int),
        ],
        responses={200: TestimonialListSerializer(many=True)},
        tags=['Отзывы'],
    )
    def get(self, request):
        qs = Testimonial.objects.filter(status=PublicationStatus.PUBLISHED)
        if request.query_params.get('featured') == 'true':
            qs = qs.filter(is_featured=True)
        limit = int(request.query_params.get('limit', 50))
        offset = int(request.query_params.get('offset', 0))
        qs = qs[offset:offset + limit]
        serializer = TestimonialListSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)

    @extend_schema(
        summary='Создать отзыв',
        request=TestimonialCreateSerializer,
        responses={
            201: TestimonialCreateResponseSerializer,
            400: OpenApiResponse(description='Ошибки валидации'),
        },
        tags=['Отзывы'],
    )
    def post(self, request):
        serializer = TestimonialCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        base_slug = slugify(f"{data['person_name']} {uuid.uuid4().hex[:8]}")[:60] or 'testimonial'
        # Используем общий генератор для единообразия slug'ов
        slug = Publication.generate_unique_slug(base_slug)

        testimonial = Testimonial.objects.create(
            person_name=data['person_name'],
            person_position=data.get('person_position') or '',
            company_name=data.get('company_name') or '',
            quote=data['quote'],
            rating=data.get('rating'),
            slug=slug,
            status=PublicationStatus.ON_MODERATION,
        )
        response_serializer = TestimonialCreateResponseSerializer(testimonial)
        return Response(response_serializer.data, status=HTTP_201_CREATED)


class TestimonialFeaturedView(APIView):
    """Избранные отзывы для главной."""

    authentication_classes: list = []
    permission_classes: list = []
    renderer_classes = [JSONRenderer]

    @extend_schema(
        summary='Избранные отзывы',
        responses={200: TestimonialListSerializer(many=True)},
        tags=['Отзывы'],
    )
    def get(self, request):
        qs = Testimonial.objects.filter(
            status=PublicationStatus.PUBLISHED,
            is_featured=True,
        )[:10]
        serializer = TestimonialListSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)

