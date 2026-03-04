from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from .choices import PublicationStatus, PublicationType


class Category(models.Model):
    """Категория для публикаций и кейсов."""

    name = models.CharField(max_length=255, verbose_name='Название')
    slug = models.SlugField(max_length=255, unique=True, verbose_name='Slug')
    description = models.TextField(blank=True, verbose_name='Описание')
    sort_order = models.IntegerField(default=0, verbose_name='Порядок сортировки')
    category_type = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Тип категории',
        help_text='Для новостей/публикаций или общий',
    )

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['sort_order', 'name']

    def __str__(self) -> str:
        return self.name


class Tag(models.Model):
    """Тег для публикаций и кейсов."""

    name = models.CharField(max_length=255, verbose_name='Название')
    slug = models.SlugField(max_length=255, unique=True, verbose_name='Slug')

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ['name']

    def __str__(self) -> str:
        return self.name


class Publication(models.Model):
    """
    Публикация (новость или статья).

    Кейсы и отзывы вынесены в отдельные модели Case и Testimonial.
    """

    type = models.CharField(
        max_length=20,
        choices=PublicationType.CHOICES,
        verbose_name='Тип',
        db_index=True,
        help_text='Тип публикации: новость или статья.',
    )
    title = models.CharField(max_length=500, verbose_name='Заголовок')
    slug = models.SlugField(max_length=500, unique=True, verbose_name='Slug', db_index=True)
    short_description = models.TextField(blank=True, verbose_name='Краткое описание')
    content = models.TextField(blank=True, verbose_name='Содержимое')

    status = models.CharField(
        max_length=20,
        choices=PublicationStatus.CHOICES,
        default=PublicationStatus.DRAFT,
        verbose_name='Статус',
        db_index=True,
    )
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Дата публикации',
        db_index=True,
    )
    main_image = models.ImageField(
        upload_to='publications/%Y/%m/',
        blank=True,
        null=True,
        verbose_name='Основное изображение',
    )
    is_featured = models.BooleanField(default=False, verbose_name='На главной', db_index=True)
    sort_order = models.IntegerField(default=0, verbose_name='Порядок сортировки')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_publications',
        verbose_name='Создал',
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_publications',
        verbose_name='Обновил',
    )

    meta_title = models.CharField(max_length=255, blank=True, verbose_name='SEO заголовок')
    meta_description = models.TextField(blank=True, verbose_name='SEO описание')

    categories = models.ManyToManyField(
        Category,
        blank=True,
        related_name='publications',
        verbose_name='Категории',
    )
    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name='publications',
        verbose_name='Теги',
    )

    class Meta:
        verbose_name = 'Публикация'
        verbose_name_plural = 'Публикации'
        ordering = ['-published_at', 'sort_order']

    def __str__(self) -> str:
        return self.title

    def get_absolute_url(self):
        from django.urls import reverse

        return reverse('publication-detail', kwargs={'slug': self.slug})

    @staticmethod
    def generate_unique_slug(base_slug: str) -> str:
        """Генерирует уникальный slug для публикаций."""
        slug = base_slug
        counter = 0
        while Publication.objects.filter(slug=slug).exists():
            counter += 1
            slug = f'{base_slug}-{counter}'
        return slug


class Case(models.Model):
    """Кейс реализованного проекта."""

    title = models.CharField(max_length=500, verbose_name='Заголовок')
    slug = models.SlugField(max_length=500, unique=True, verbose_name='Slug', db_index=True)
    short_description = models.TextField(blank=True, verbose_name='Краткое описание')
    content = models.TextField(blank=True, verbose_name='Содержимое')

    client_company = models.CharField(max_length=255, verbose_name='Компания клиента')
    client_industry = models.CharField(max_length=255, blank=True, verbose_name='Отрасль')
    services = models.TextField(blank=True, verbose_name='Услуги/курсы')
    results_short = models.TextField(blank=True, verbose_name='Краткий результат')
    results_detailed = models.TextField(blank=True, verbose_name='Подробные результаты')
    metrics = models.TextField(blank=True, verbose_name='Метрики')

    main_image = models.ImageField(
        upload_to='publications/cases/%Y/%m/',
        blank=True,
        null=True,
        verbose_name='Основное изображение',
    )

    status = models.CharField(
        max_length=20,
        choices=PublicationStatus.CHOICES,
        default=PublicationStatus.DRAFT,
        verbose_name='Статус',
        db_index=True,
    )
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Дата публикации',
        db_index=True,
    )
    is_featured = models.BooleanField(default=False, verbose_name='На главной', db_index=True)
    sort_order = models.IntegerField(default=0, verbose_name='Порядок сортировки')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_cases',
        verbose_name='Создал',
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_cases',
        verbose_name='Обновил',
    )

    meta_title = models.CharField(max_length=255, blank=True, verbose_name='SEO заголовок')
    meta_description = models.TextField(blank=True, verbose_name='SEO описание')

    categories = models.ManyToManyField(
        Category,
        blank=True,
        related_name='cases',
        verbose_name='Категории',
    )
    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name='cases',
        verbose_name='Теги',
    )

    class Meta:
        verbose_name = 'Кейс'
        verbose_name_plural = 'Кейсы'
        ordering = ['-published_at', 'sort_order']

    def __str__(self) -> str:
        return self.title


class Testimonial(models.Model):
    """Отзыв клиента."""

    person_name = models.CharField(max_length=255, verbose_name='ФИО')
    person_position = models.CharField(max_length=255, blank=True, verbose_name='Должность')
    company_name = models.CharField(max_length=255, blank=True, verbose_name='Компания')
    quote = models.TextField(verbose_name='Текст отзыва')
    rating = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name='Оценка (1-5)',
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    company_logo = models.ImageField(
        upload_to='publications/testimonials/%Y/%m/',
        blank=True,
        null=True,
        verbose_name='Логотип компании',
    )

    slug = models.SlugField(
        max_length=500,
        unique=True,
        verbose_name='Slug',
        db_index=True,
        help_text='Slug отзыва для публичного API.',
    )

    status = models.CharField(
        max_length=20,
        choices=PublicationStatus.CHOICES,
        default=PublicationStatus.ON_MODERATION,
        verbose_name='Статус',
        db_index=True,
    )
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Дата публикации',
        db_index=True,
    )
    is_featured = models.BooleanField(default=False, verbose_name='На главной', db_index=True)
    sort_order = models.IntegerField(default=0, verbose_name='Порядок сортировки')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_testimonials',
        verbose_name='Создал',
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_testimonials',
        verbose_name='Обновил',
    )

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        ordering = ['-created_at']

    def __str__(self) -> str:
        base = self.person_name or 'Отзыв'
        if self.company_name:
            return f'{base} — {self.company_name}'
        return base

