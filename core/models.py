from django.db import models

from .choices import (
    ApplicationStatus,
    CourseBatchStatus,
    DirectionStatus,
    LearningFormatStatus,
    ProgramStatus,
    ProgramType,
)


class Direction(models.Model):
    """Направление (категория программ)"""
    name = models.CharField(
        max_length=255,
        unique=True,
        verbose_name='Название'
    )
    short_description = models.TextField(
        blank=True,
        verbose_name='Краткое описание'
    )
    sort_order = models.IntegerField(
        default=0,
        verbose_name='Порядок сортировки'
    )
    status = models.CharField(
        max_length=20,
        choices=DirectionStatus.CHOICES,
        default=DirectionStatus.ACTIVE,
        verbose_name='Статус'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )

    class Meta:
        verbose_name = 'Направление'
        verbose_name_plural = 'Направления'
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name


class LearningFormat(models.Model):
    """Форма обучения"""
    name = models.CharField(
        max_length=255,
        unique=True,
        verbose_name='Название'
    )
    short_description = models.TextField(
        blank=True,
        verbose_name='Краткое описание'
    )
    full_description = models.TextField(
        blank=True,
        verbose_name='Подробное описание'
    )
    sort_order = models.IntegerField(
        default=0,
        verbose_name='Порядок сортировки'
    )
    status = models.CharField(
        max_length=20,
        choices=LearningFormatStatus.CHOICES,
        default=LearningFormatStatus.ACTIVE,
        verbose_name='Статус'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )

    class Meta:
        verbose_name = 'Форма обучения'
        verbose_name_plural = 'Формы обучения'
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name


class Program(models.Model):
    """Программа повышения квалификации"""
    name = models.CharField(
        max_length=255,
        verbose_name='Название',
        help_text='Название программы повышения квалификации'
    )
    direction = models.ForeignKey(
        Direction,
        on_delete=models.CASCADE,
        related_name='programs',
        verbose_name='Направление',
        help_text='ID направления (категории) программы'
    )
    program_type = models.CharField(
        max_length=30,
        choices=ProgramType.CHOICES,
        verbose_name='Вид программы',
        help_text='Вид программы: повышение квалификации или переподготовка'
    )
    training_direction_code = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Код направления подготовки',
        help_text='Код направления подготовки'
    )
    lead = models.TextField(
        verbose_name='Лид',
        help_text='Краткое описание программы (лид)'
    )
    about_description = models.TextField(
        verbose_name='Описание "О программе"',
        help_text='Подробное описание программы ("О программе")'
    )
    curriculum = models.TextField(
        verbose_name='Программа обучения (учебный план)',
        help_text='Программа обучения (учебный план)'
    )
    target_audience = models.TextField(
        verbose_name='Целевая аудитория',
        help_text='Описание целевой аудитории программы'
    )
    enrollment_process = models.TextField(
        blank=True,
        verbose_name='Порядок зачисления',
        help_text='Порядок зачисления на программу'
    )
    learning_format = models.ForeignKey(
        LearningFormat,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='programs',
        verbose_name='Форма обучения',
        help_text='Форма обучения (например: "Очная", "Онлайн")'
    )
    learning_format_comment = models.TextField(
        blank=True,
        verbose_name='Комментарий к форме обучения',
        help_text='Комментарий к форме обучения (например: "Программа может быть также реализована заочно")'
    )
    hours_volume = models.PositiveIntegerField(
        verbose_name='Объём программы в часах',
        help_text='Объём программы в академических часах'
    )
    duration = models.CharField(
        max_length=255,
        verbose_name='Календарная длительность',
        help_text='Календарная длительность программы (например: "2 месяца", "72 часа")'
    )
    cost = models.CharField(
        max_length=255,
        verbose_name='Стоимость',
        help_text='Стоимость программы (например: "10000 руб", "Бесплатно")'
    )
    outcome = models.TextField(
        blank=True,
        verbose_name='Итог по программе',
        help_text='Итог по программе (что получает слушатель после завершения)'
    )
    requirements = models.TextField(
        blank=True,
        verbose_name='Требования к слушателям',
        help_text='Требования к слушателям для зачисления на программу'
    )
    learning_outcomes = models.TextField(
        blank=True,
        verbose_name='Результаты обучения',
        help_text='Результаты обучения (компетенции, которые приобретает слушатель)'
    )
    status = models.CharField(
        max_length=20,
        choices=ProgramStatus.CHOICES,
        default=ProgramStatus.DRAFT,
        verbose_name='Статус',
        help_text='Статус программы: "draft" (черновик), "active" (активен), "archived" (архив)'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания',
        help_text='Дата и время создания записи программы'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления',
        help_text='Дата и время последнего обновления записи программы'
    )

    class Meta:
        verbose_name = 'Программа'
        verbose_name_plural = 'Программы'
        ordering = ['name']

    def __str__(self):
        return self.name


class CourseBatch(models.Model):
    """Поток/Набор программы"""
    program = models.ForeignKey(
        Program,
        on_delete=models.CASCADE,
        related_name='batches',
        verbose_name='Программа'
    )
    name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Название/номер потока'
    )
    start_date = models.DateField(
        verbose_name='Дата начала'
    )
    end_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='Дата окончания'
    )
    learning_format = models.ForeignKey(
        LearningFormat,
        on_delete=models.CASCADE,
        related_name='batches',
        verbose_name='Форма проведения'
    )
    schedule = models.TextField(
        blank=True,
        verbose_name='Расписание'
    )
    seats_count = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name='Количество мест'
    )
    cost = models.CharField(
        max_length=255,
        default='0',
        blank=True,
        verbose_name='Стоимость',
        help_text='Стоимость потока (например: "15000 руб", "Бесплатно")'
    )
    status = models.CharField(
        max_length=20,
        choices=CourseBatchStatus.CHOICES,
        default=CourseBatchStatus.ENROLLMENT_OPEN,
        verbose_name='Статус'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )

    class Meta:
        verbose_name = 'Поток/Набор'
        verbose_name_plural = 'Потоки/Наборы'
        ordering = ['-start_date']

    def __str__(self):
        if self.name:
            return self.name
        return f'Поток {self.program.name} - {self.start_date}'


class Application(models.Model):
    """Заявка слушателя на обучение"""
    full_name = models.CharField(
        max_length=255,
        verbose_name='ФИО'
    )
    program = models.ForeignKey(
        Program,
        on_delete=models.CASCADE,
        related_name='applications',
        verbose_name='Программа'
    )
    batch = models.ForeignKey(
        CourseBatch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='applications',
        verbose_name='Поток'
    )
    email = models.EmailField(
        verbose_name='Email'
    )
    phone = models.CharField(
        max_length=50,
        verbose_name='Телефон'
    )
    comment = models.TextField(
        blank=True,
        verbose_name='Комментарий'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    status = models.CharField(
        max_length=20,
        choices=ApplicationStatus.CHOICES,
        default=ApplicationStatus.NEW,
        verbose_name='Статус'
    )
    admin_comment = models.TextField(
        blank=True,
        verbose_name='Комментарий администратора'
    )

    class Meta:
        verbose_name = 'Заявка слушателя'
        verbose_name_plural = 'Заявки слушателей'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.full_name} — {self.program.name}'


class CallbackRequest(models.Model):
    """Запрос на обратный звонок"""
    name = models.CharField(max_length=255, verbose_name='Имя')
    phone = models.CharField(max_length=50, verbose_name='Телефон')
    email = models.EmailField(verbose_name='Email')
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )

    class Meta:
        verbose_name = 'Запрос обратного звонка'
        verbose_name_plural = 'Запросы обратного звонка'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} — {self.phone}'
