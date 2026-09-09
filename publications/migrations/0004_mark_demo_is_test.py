from django.db import migrations


def mark_demo_publications(apps, schema_editor):
    Category = apps.get_model('publications', 'Category')
    Tag = apps.get_model('publications', 'Tag')
    Publication = apps.get_model('publications', 'Publication')
    Case = apps.get_model('publications', 'Case')
    Testimonial = apps.get_model('publications', 'Testimonial')

    Category.objects.filter(
        slug__in=[
            'novosti-centra',
            'stati-ekspertov',
            'korporativnoe-obuchenie',
        ]
    ).update(is_test=True)
    Tag.objects.filter(
        slug__in=[
            'povyshenie-kvalifikacii',
            'onlayn',
            'korporativnym-klientam',
            'it',
        ]
    ).update(is_test=True)
    Publication.objects.filter(slug__startswith='demo-').update(is_test=True)
    Case.objects.filter(slug__startswith='demo-').update(is_test=True)
    Testimonial.objects.filter(slug__startswith='demo-').update(is_test=True)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('publications', '0003_setting_and_is_test'),
    ]

    operations = [
        migrations.RunPython(mark_demo_publications, noop_reverse),
    ]
