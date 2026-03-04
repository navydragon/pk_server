# Generated manually

from django.db import migrations, models


def set_default_program_type(apps, schema_editor):
    """Устанавливает дефолтное значение 'pk' для существующих записей"""
    Program = apps.get_model('core', 'Program')
    Program.objects.filter(program_type__isnull=True).update(program_type='pk')


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_alter_learningformat_options_and_more'),
    ]

    operations = [
        # Добавляем поле program_type с временным null=True для существующих записей
        migrations.AddField(
            model_name='program',
            name='program_type',
            field=models.CharField(
                choices=[('pk', 'Повышение квалификации'), ('pp', 'Переподготовка')],
                max_length=30,
                null=True,
                verbose_name='Вид программы'
            ),
        ),
        # Устанавливаем дефолтное значение для существующих записей
        migrations.RunPython(set_default_program_type, migrations.RunPython.noop),
        # Делаем поле обязательным
        migrations.AlterField(
            model_name='program',
            name='program_type',
            field=models.CharField(
                choices=[('pk', 'Повышение квалификации'), ('pp', 'Переподготовка')],
                max_length=30,
                verbose_name='Вид программы',
                help_text='Вид программы: повышение квалификации или переподготовка'
            ),
        ),
        # Добавляем поле training_direction_code
        migrations.AddField(
            model_name='program',
            name='training_direction_code',
            field=models.CharField(
                blank=True,
                max_length=100,
                verbose_name='Код направления подготовки',
                help_text='Код направления подготовки'
            ),
        ),
    ]
