# Generated manually for CRM appeals module

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0008_add_program_position'),
    ]

    operations = [
        migrations.AddField(
            model_name='application',
            name='assigned_to',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='assigned_applications',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Ответственный',
            ),
        ),
        migrations.AddField(
            model_name='application',
            name='preferred_contact',
            field=models.CharField(
                blank=True,
                choices=[
                    ('phone', 'Телефон'),
                    ('email', 'Email'),
                    ('messenger', 'Мессенджер'),
                ],
                max_length=20,
                verbose_name='Предпочтительный способ связи',
            ),
        ),
        migrations.AddField(
            model_name='application',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='Дата обновления'),
        ),
        migrations.AddField(
            model_name='callbackrequest',
            name='admin_comment',
            field=models.TextField(blank=True, verbose_name='Комментарий администратора'),
        ),
        migrations.AddField(
            model_name='callbackrequest',
            name='assigned_to',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='assigned_callback_requests',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Ответственный',
            ),
        ),
        migrations.AddField(
            model_name='callbackrequest',
            name='comment',
            field=models.TextField(blank=True, verbose_name='Комментарий/вопрос'),
        ),
        migrations.AddField(
            model_name='callbackrequest',
            name='request_type',
            field=models.CharField(
                blank=True,
                choices=[
                    ('individual', 'Физическое лицо'),
                    ('organization', 'Организация'),
                ],
                max_length=20,
                verbose_name='Тип обращения',
            ),
        ),
        migrations.AddField(
            model_name='callbackrequest',
            name='status',
            field=models.CharField(
                choices=[
                    ('new', 'Новый'),
                    ('processed', 'Обработан'),
                    ('closed', 'Закрыт'),
                ],
                default='new',
                max_length=20,
                verbose_name='Статус',
            ),
        ),
        migrations.AddField(
            model_name='callbackrequest',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='Дата обновления'),
        ),
        migrations.AlterField(
            model_name='callbackrequest',
            name='email',
            field=models.EmailField(blank=True, max_length=254, verbose_name='Email'),
        ),
        migrations.CreateModel(
            name='CorporateRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('organization_name', models.CharField(max_length=255, verbose_name='Название организации')),
                ('contact_name', models.CharField(max_length=255, verbose_name='ФИО контактного лица')),
                ('contact_position', models.CharField(blank=True, max_length=255, verbose_name='Должность контактного лица')),
                ('phone', models.CharField(max_length=50, verbose_name='Телефон')),
                ('email', models.EmailField(max_length=254, verbose_name='Email')),
                ('topics', models.TextField(verbose_name='Интересующие направления/темы')),
                ('employees_count', models.PositiveIntegerField(verbose_name='Ориентировочное количество сотрудников')),
                ('desired_dates', models.CharField(blank=True, max_length=255, verbose_name='Желаемые сроки')),
                ('comment', models.TextField(blank=True, verbose_name='Дополнительные комментарии')),
                ('status', models.CharField(
                    choices=[
                        ('new', 'Новый'),
                        ('in_progress', 'В работе'),
                        ('quote_sent', 'КП отправлено'),
                        ('closed', 'Закрыт'),
                    ],
                    default='new',
                    max_length=20,
                    verbose_name='Статус',
                )),
                ('admin_comment', models.TextField(blank=True, verbose_name='Комментарий администратора')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Дата обновления')),
                ('assigned_to', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='assigned_corporate_requests',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Ответственный',
                )),
                ('directions', models.ManyToManyField(
                    blank=True,
                    related_name='corporate_requests',
                    to='core.direction',
                    verbose_name='Направления',
                )),
                ('programs', models.ManyToManyField(
                    blank=True,
                    related_name='corporate_requests',
                    to='core.program',
                    verbose_name='Программы',
                )),
            ],
            options={
                'verbose_name': 'Корпоративный запрос',
                'verbose_name_plural': 'Корпоративные запросы',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='StaffProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('full_name', models.CharField(max_length=255, verbose_name='ФИО')),
                ('role', models.CharField(
                    choices=[
                        ('administrator', 'Администратор'),
                        ('methodist', 'Методист'),
                        ('editor', 'Редактор'),
                    ],
                    default='editor',
                    max_length=20,
                    verbose_name='Роль',
                )),
                ('is_active', models.BooleanField(default=True, verbose_name='Активен')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('last_login_at', models.DateTimeField(blank=True, null=True, verbose_name='Дата последнего входа')),
                ('user', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='staff_profile',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Пользователь',
                )),
            ],
            options={
                'verbose_name': 'Профиль сотрудника',
                'verbose_name_plural': 'Профили сотрудников',
                'ordering': ['full_name'],
            },
        ),
    ]
