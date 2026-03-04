"""
Choices для моделей публикаций, кейсов и отзывов.
"""


class PublicationType:
    """Типы публикаций (только новости и статьи)."""

    NEWS = 'news'
    ARTICLE = 'article'

    CHOICES = [
        (NEWS, 'Новость'),
        (ARTICLE, 'Статья'),
    ]


class PublicationStatus:
    """Статусы публикации/кейса/отзыва."""

    DRAFT = 'draft'
    ON_MODERATION = 'on_moderation'
    PUBLISHED = 'published'
    ARCHIVED = 'archived'

    CHOICES = [
        (DRAFT, 'Черновик'),
        (ON_MODERATION, 'На модерации'),
        (PUBLISHED, 'Опубликовано'),
        (ARCHIVED, 'Архив'),
    ]

