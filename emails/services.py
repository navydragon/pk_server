"""Сервисы отправки email-уведомлений."""

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string


def send_application_notification(application):
    """
    Отправляет уведомление о новой заявке на email из NOTIFICATION_EMAIL.

    Не отправляет письмо, если NOTIFICATION_EMAIL не задан.
    """
    recipient = getattr(settings, 'NOTIFICATION_EMAIL', '') or ''
    if not recipient:
        return 0

    context = {
        'full_name': application.full_name,
        'program_name': application.program.name,
        'batch_info': str(application.batch) if application.batch else 'Не указан',
        'email': application.email,
        'phone': application.phone,
        'comment': application.comment or '—',
        'created_at': application.created_at.strftime('%d.%m.%Y %H:%M'),
    }

    subject = f'Новая заявка: {application.full_name} — {application.program.name}'
    message = render_to_string('emails/application_created.txt', context)

    return send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[recipient],
        fail_silently=False,
    )


def send_callback_request_notification(callback_request):
    """
    Отправляет уведомление о запросе обратного звонка на email из NOTIFICATION_EMAIL.

    Не отправляет письмо, если NOTIFICATION_EMAIL не задан.
    """
    recipient = getattr(settings, 'NOTIFICATION_EMAIL', '') or ''
    if not recipient:
        return 0

    context = {
        'name': callback_request.name,
        'phone': callback_request.phone,
        'email': callback_request.email,
        'created_at': callback_request.created_at.strftime('%d.%m.%Y %H:%M'),
    }

    subject = f'Запрос обратного звонка: {callback_request.name}'
    message = render_to_string('emails/callback_request_created.txt', context)

    return send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[recipient],
        fail_silently=False,
    )
