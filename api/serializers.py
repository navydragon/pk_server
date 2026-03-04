from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from core.choices import ApplicationStatus, CourseBatchStatus
from core.models import Application, CallbackRequest, CourseBatch, Program
from publications.choices import PublicationStatus, PublicationType
from publications.models import Case, Publication, Testimonial


class ProgramSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Program"""
    direction_name = serializers.CharField(
        source='direction.name',
        read_only=True,
        help_text='Название направления программы'
    )
    learning_format = serializers.StringRelatedField(
        read_only=True,
        help_text='Форма обучения (например: "Очная", "Онлайн")'
    )

    class Meta:
        model = Program
        fields = [
            'id',
            'name',
            'direction',
            'direction_name',
            'program_type',
            'training_direction_code',
            'lead',
            'about_description',
            'curriculum',
            'target_audience',
            'enrollment_process',
            'learning_format',
            'learning_format_comment',
            'hours_volume',
            'duration',
            'cost',
            'outcome',
            'requirements',
            'learning_outcomes',
            'status',
            'created_at',
            'updated_at',
        ]
        extra_kwargs = {
            'id': {
                'help_text': 'Уникальный идентификатор программы'
            },
        }


class CourseBatchSerializer(serializers.ModelSerializer):
    """Сериализатор для модели CourseBatch"""
    learning_format = serializers.StringRelatedField(
        read_only=True,
        help_text='Форма обучения потока'
    )
    enrollment_status_text = serializers.SerializerMethodField(
        help_text='Текст статуса записи'
    )
    action_button_text = serializers.SerializerMethodField(
        help_text='Текст кнопки действия'
    )
    is_action_enabled = serializers.SerializerMethodField(
        help_text='Доступность действия (записи)'
    )

    class Meta:
        model = CourseBatch
        fields = [
            'id',
            'start_date',
            'end_date',
            'learning_format',
            'cost',
            'status',
            'enrollment_status_text',
            'action_button_text',
            'is_action_enabled',
        ]

    @extend_schema_field(serializers.CharField())
    def get_enrollment_status_text(self, obj):
        """Возвращает текст статуса записи на основе status"""
        status_mapping = {
            CourseBatchStatus.ENROLLMENT_OPEN: 'Открыта запись',
            CourseBatchStatus.ENROLLMENT_CLOSED: 'Запись закрыта',
            CourseBatchStatus.COMPLETED: 'Набор завершен',
            CourseBatchStatus.IN_PROGRESS: 'Идет обучение',
            CourseBatchStatus.CANCELLED: 'Отменен',
        }
        return status_mapping.get(obj.status, 'Неизвестный статус')

    @extend_schema_field(serializers.CharField())
    def get_action_button_text(self, obj):
        """Возвращает текст кнопки действия на основе status"""
        status_mapping = {
            CourseBatchStatus.ENROLLMENT_OPEN: 'Записаться',
            CourseBatchStatus.ENROLLMENT_CLOSED: 'Запись закрыта',
            CourseBatchStatus.COMPLETED: 'Набор завершен',
            CourseBatchStatus.IN_PROGRESS: 'Идет обучение',
            CourseBatchStatus.CANCELLED: 'Отменен',
        }
        return status_mapping.get(obj.status, 'Неизвестный статус')

    @extend_schema_field(serializers.BooleanField())
    def get_is_action_enabled(self, obj):
        """Возвращает доступность действия (только для enrollment_open)"""
        return obj.status == CourseBatchStatus.ENROLLMENT_OPEN


class ProgramWithBatchesSerializer(serializers.ModelSerializer):
    """Сериализатор для программы с потоками"""
    direction_name = serializers.CharField(
        source='direction.name',
        read_only=True,
        help_text='Название направления (категория) программы'
    )
    learning_format = serializers.StringRelatedField(
        read_only=True,
        help_text='Форма обучения программы (например: "Очная", "Онлайн")'
    )
    batches = CourseBatchSerializer(
        many=True,
        read_only=True,
        help_text='Список потоков программы'
    )

    class Meta:
        model = Program
        fields = [
            'id',
            'name',
            'direction_name',
            'learning_format',
            'hours_volume',
            'batches',
        ]


class ProgramDetailSerializer(serializers.ModelSerializer):
    """Сериализатор для детального просмотра программы с потоками"""
    direction_name = serializers.CharField(
        source='direction.name',
        read_only=True,
        help_text='Название направления программы'
    )
    learning_format = serializers.StringRelatedField(
        read_only=True,
        help_text='Форма обучения (например: "Очная", "Онлайн")'
    )
    batches = CourseBatchSerializer(
        many=True,
        read_only=True,
        help_text='Список текущих и будущих потоков программы (дата начала >= текущей даты)'
    )

    class Meta:
        model = Program
        fields = [
            'id',
            'name',
            'direction',
            'direction_name',
            'program_type',
            'training_direction_code',
            'lead',
            'about_description',
            'curriculum',
            'target_audience',
            'enrollment_process',
            'learning_format',
            'learning_format_comment',
            'hours_volume',
            'duration',
            'outcome',
            'requirements',
            'learning_outcomes',
            'status',
            'created_at',
            'updated_at',
            'batches',
        ]
        extra_kwargs = {
            'id': {
                'help_text': 'Уникальный идентификатор программы'
            },
        }


class ApplicationCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания заявки слушателя."""
    program_name = serializers.CharField(source='program.name', read_only=True)

    class Meta:
        model = Application
        fields = ['id', 'full_name', 'program', 'program_name', 'batch', 'email', 'phone', 'comment', 'created_at']
        extra_kwargs = {
            'id': {'read_only': True},
            'created_at': {'read_only': True},
            'batch': {'required': False, 'allow_null': True},
            'comment': {'required': False, 'allow_blank': True},
        }

    def validate(self, attrs):
        program = attrs.get('program')
        batch = attrs.get('batch')

        if batch and batch.program_id != program.id:
            raise serializers.ValidationError({
                'batch': 'Выбранный поток не относится к выбранной программе.'
            })
        return attrs

    def create(self, validated_data):
        validated_data['status'] = ApplicationStatus.NEW
        return super().create(validated_data)


class CallbackRequestCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания запроса обратного звонка."""

    class Meta:
        model = CallbackRequest
        fields = ['id', 'name', 'phone', 'email', 'created_at']
        extra_kwargs = {
            'id': {'read_only': True},
            'created_at': {'read_only': True},
        }


# --- Publications API ---

class PublicationListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка публикаций."""
    main_image_url = serializers.SerializerMethodField()

    class Meta:
        model = Publication
        fields = [
            'id', 'type', 'title', 'slug', 'short_description',
            'main_image_url', 'published_at', 'is_featured',
        ]

    @extend_schema_field(serializers.URLField())
    def get_main_image_url(self, obj):
        if obj.main_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.main_image.url)
            return obj.main_image.url
        return None


class PublicationDetailSerializer(serializers.ModelSerializer):
    """Сериализатор для детальной публикации."""
    main_image_url = serializers.SerializerMethodField()
    categories = serializers.StringRelatedField(many=True, read_only=True)
    tags = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = Publication
        fields = [
            'id', 'type', 'title', 'slug', 'short_description', 'content',
            'main_image_url', 'published_at', 'is_featured',
            'meta_title', 'meta_description',
            'categories', 'tags',
        ]

    @extend_schema_field(serializers.URLField())
    def get_main_image_url(self, obj):
        if obj.main_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.main_image.url)
            return obj.main_image.url
        return None


class CaseListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка кейсов."""
    main_image_url = serializers.SerializerMethodField()

    class Meta:
        model = Case
        fields = [
            'id',
            'title',
            'slug',
            'client_company',
            'short_description',
            'main_image_url',
            'published_at',
            'is_featured',
        ]

    @extend_schema_field(serializers.URLField())
    def get_main_image_url(self, obj):
        if obj.main_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.main_image.url)
            return obj.main_image.url
        return None


class CaseDetailSerializer(serializers.ModelSerializer):
    """Сериализатор для детального кейса."""
    main_image_url = serializers.SerializerMethodField()
    categories = serializers.StringRelatedField(many=True, read_only=True)
    tags = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = Case
        fields = [
            'id',
            'title',
            'slug',
            'short_description',
            'content',
            'client_company',
            'client_industry',
            'services',
            'results_short',
            'results_detailed',
            'metrics',
            'main_image_url',
            'published_at',
            'is_featured',
            'meta_title',
            'meta_description',
            'categories',
            'tags',
        ]

    @extend_schema_field(serializers.URLField())
    def get_main_image_url(self, obj):
        if obj.main_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.main_image.url)
            return obj.main_image.url
        return None


class TestimonialListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка отзывов."""

    class Meta:
        model = Testimonial
        fields = [
            'id',
            'person_name',
            'person_position',
            'company_name',
            'rating',
            'is_featured',
            'created_at',
        ]


class TestimonialDetailSerializer(serializers.ModelSerializer):
    """Сериализатор для детального отзыва."""
    company_logo_url = serializers.SerializerMethodField()

    class Meta:
        model = Testimonial
        fields = [
            'id',
            'person_name',
            'person_position',
            'company_name',
            'quote',
            'rating',
            'company_logo_url',
            'status',
            'published_at',
            'is_featured',
            'sort_order',
            'slug',
        ]

    @extend_schema_field(serializers.URLField())
    def get_company_logo_url(self, obj):
        if obj.company_logo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.company_logo.url)
            return obj.company_logo.url
        return None


class TestimonialCreateSerializer(serializers.Serializer):
    """Сериализатор для создания отзыва через API."""
    person_name = serializers.CharField(max_length=255)
    quote = serializers.CharField()
    person_position = serializers.CharField(max_length=255, required=False, allow_blank=True)
    company_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    rating = serializers.IntegerField(min_value=1, max_value=5, required=False, allow_null=True)


class TestimonialCreateResponseSerializer(serializers.ModelSerializer):
    """Сериализатор ответа при создании отзыва."""

    class Meta:
        model = Testimonial
        fields = ['id', 'slug', 'status', 'person_name', 'company_name', 'quote', 'rating', 'created_at']

