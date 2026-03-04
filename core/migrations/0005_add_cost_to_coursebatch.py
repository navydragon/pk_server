# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_add_program_type_and_training_direction_code'),
    ]

    operations = [
        migrations.AddField(
            model_name='coursebatch',
            name='cost',
            field=models.CharField(
                blank=True,
                default='0',
                max_length=255,
                verbose_name='Стоимость',
                help_text='Стоимость потока (например: "15000 руб", "Бесплатно")'
            ),
        ),
    ]
