from django.db import migrations


def seed_settings_and_mark_demo(apps, schema_editor):
    Setting = apps.get_model('core', 'Setting')
    Setting.objects.get_or_create(code='show_test_data', defaults={'value': 'false'})

    Direction = apps.get_model('core', 'Direction')
    LearningFormat = apps.get_model('core', 'LearningFormat')
    Program = apps.get_model('core', 'Program')
    CourseBatch = apps.get_model('core', 'CourseBatch')
    Application = apps.get_model('core', 'Application')
    CallbackRequest = apps.get_model('core', 'CallbackRequest')
    CorporateRequest = apps.get_model('core', 'CorporateRequest')

    demo_direction_names = [
        'Программирование и IT',
        'Бизнес-анализ',
        'Финансы и бухгалтерия',
        'Маркетинг и реклама',
        'Управление проектами',
        'Дизайн',
        'Архивное направление',
    ]
    demo_format_names = [
        'Очный',
        'Онлайн с преподавателем',
        'Заочный',
        'Смешанный (очно-онлайн)',
    ]

    Direction.objects.filter(name__in=demo_direction_names).update(is_test=True)
    LearningFormat.objects.filter(name__in=demo_format_names).update(is_test=True)
    Program.objects.filter(training_direction_code__startswith='DEMO-').update(is_test=True)
    CourseBatch.objects.filter(name__startswith='Демо-поток').update(is_test=True)
    Application.objects.filter(email__endswith='@demo.local').update(is_test=True)
    CallbackRequest.objects.filter(email__endswith='@demo.local').update(is_test=True)
    CallbackRequest.objects.filter(phone__startswith='+79001').update(is_test=True)
    CorporateRequest.objects.filter(email__endswith='@demo.local').update(is_test=True)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_setting_and_is_test'),
    ]

    operations = [
        migrations.RunPython(seed_settings_and_mark_demo, noop_reverse),
    ]
