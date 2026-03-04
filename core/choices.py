"""
Choices для статусов моделей каталога
"""


class DirectionStatus:
    """Статусы направления"""
    ACTIVE = 'active'
    ARCHIVED = 'archived'
    
    CHOICES = [
        (ACTIVE, 'Активен'),
        (ARCHIVED, 'Архив'),
    ]


class LearningFormatStatus:
    """Статусы формы обучения"""
    ACTIVE = 'active'
    ARCHIVED = 'archived'
    
    CHOICES = [
        (ACTIVE, 'Активен'),
        (ARCHIVED, 'Архив'),
    ]


class ProgramStatus:
    """Статусы программы"""
    DRAFT = 'draft'
    ACTIVE = 'active'
    ARCHIVED = 'archived'
    
    CHOICES = [
        (DRAFT, 'Черновик'),
        (ACTIVE, 'Активен'),
        (ARCHIVED, 'Архив'),
    ]


class ProgramType:
    """Виды программы"""
    QUALIFICATION_UPGRADE = 'pk'
    RETRAINING = 'pp'
    
    CHOICES = [
        (QUALIFICATION_UPGRADE, 'Повышение квалификации'),
        (RETRAINING, 'Переподготовка'),
    ]


class CourseBatchStatus:
    """Статусы потока/набора"""
    ENROLLMENT_OPEN = 'enrollment_open'
    ENROLLMENT_CLOSED = 'enrollment_closed'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'
    
    CHOICES = [
        (ENROLLMENT_OPEN, 'Набор открыт'),
        (ENROLLMENT_CLOSED, 'Набор закрыт'),
        (IN_PROGRESS, 'Идет обучение'),
        (COMPLETED, 'Завершен'),
        (CANCELLED, 'Отменен'),
    ]


class ApplicationStatus:
    """Статусы заявки слушателя"""
    NEW = 'new'
    IN_PROGRESS = 'in_progress'
    CONFIRMED = 'confirmed'
    REJECTED = 'rejected'
    COMPLETED = 'completed'

    CHOICES = [
        (NEW, 'Новая'),
        (IN_PROGRESS, 'В работе'),
        (CONFIRMED, 'Подтверждена'),
        (REJECTED, 'Отклонена'),
        (COMPLETED, 'Завершена'),
    ]
