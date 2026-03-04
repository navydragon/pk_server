# Generated manually

import django.db.models.deletion
from django.db import migrations, models


def migrate_learning_formats_to_learning_format(apps, schema_editor):
    """Переносит данные из ManyToManyField в ForeignKey (берет первую форму обучения)"""
    Program = apps.get_model('core', 'Program')
    for program in Program.objects.all():
        # Получаем первую форму обучения из ManyToMany
        learning_formats = program.learning_formats.all()
        if learning_formats.exists():
            program.learning_format = learning_formats.first()
            program.save()


def reverse_migrate_learning_format_to_learning_formats(apps, schema_editor):
    """Обратная миграция: переносит данные из ForeignKey обратно в ManyToMany"""
    Program = apps.get_model('core', 'Program')
    for program in Program.objects.all():
        if program.learning_format:
            program.learning_formats.add(program.learning_format)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        # Шаг 1: Добавляем новое поле learning_format (пока nullable)
        migrations.AddField(
            model_name='program',
            name='learning_format',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='programs_new',
                to='core.learningformat',
                verbose_name='Форма обучения'
            ),
        ),
        # Шаг 2: Переносим данные из ManyToMany в ForeignKey
        migrations.RunPython(
            migrate_learning_formats_to_learning_format,
            reverse_migrate_learning_format_to_learning_formats
        ),
        # Шаг 3: Удаляем старое ManyToMany поле
        migrations.RemoveField(
            model_name='program',
            name='learning_formats',
        ),
        # Шаг 4: Переименовываем related_name для learning_format
        migrations.AlterField(
            model_name='program',
            name='learning_format',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='programs',
                to='core.learningformat',
                verbose_name='Форма обучения'
            ),
        ),
        # Шаг 5: Добавляем поле learning_format_comment
        migrations.AddField(
            model_name='program',
            name='learning_format_comment',
            field=models.TextField(
                blank=True,
                verbose_name='Комментарий к форме обучения',
                help_text='Комментарий к форме обучения (например: "Программа может быть также реализована заочно")'
            ),
        ),
    ]
