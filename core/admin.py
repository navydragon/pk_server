from django.contrib import admin

from .models import Application, CallbackRequest, CourseBatch, Direction, LearningFormat, Program


@admin.register(Direction)
class DirectionAdmin(admin.ModelAdmin):
    """Админка для направления"""
    list_display = ('name', 'status', 'sort_order', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('name', 'short_description')
    ordering = ('sort_order', 'name')
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'short_description', 'status')
        }),
        ('Дополнительно', {
            'fields': ('sort_order', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')


@admin.register(LearningFormat)
class LearningFormatAdmin(admin.ModelAdmin):
    """Админка для формы обучения"""
    list_display = ('name', 'status', 'sort_order', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('name', 'short_description')
    ordering = ('sort_order', 'name')
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'short_description', 'full_description', 'status')
        }),
        ('Дополнительно', {
            'fields': ('sort_order', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    """Админка для программы"""
    list_display = ('position', 'name', 'direction', 'program_type', 'status', 'hours_volume', 'created_at')
    list_filter = ('status', 'direction', 'program_type', 'learning_format', 'created_at')
    search_fields = ('name', 'lead', 'target_audience')
    raw_id_fields = ('direction',)
    ordering = ('position', 'name')
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'direction', 'program_type', 'training_direction_code', 'position', 'lead', 'status')
        }),
        ('Описание', {
            'fields': ('about_description', 'curriculum', 'target_audience', 'enrollment_process')
        }),
        ('Параметры обучения', {
            'fields': ('learning_format', 'learning_format_comment', 'hours_volume', 'duration', 'cost')
        }),
        ('Дополнительно', {
            'fields': ('outcome', 'requirements', 'learning_outcomes', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')


@admin.register(CourseBatch)
class CourseBatchAdmin(admin.ModelAdmin):
    """Админка для потока/набора"""
    list_display = ('name', 'program', 'learning_format', 'start_date', 'end_date', 'cost', 'status', 'seats_count')
    list_filter = ('status', 'learning_format', 'start_date', 'program')
    search_fields = ('name', 'program__name')
    raw_id_fields = ('program', 'learning_format')
    date_hierarchy = 'start_date'
    ordering = ('-start_date',)
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('program', 'name', 'learning_format', 'status')
        }),
        ('Даты и расписание', {
            'fields': ('start_date', 'end_date', 'schedule', 'seats_count', 'cost')
        }),
        ('Дополнительно', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    """Админка для заявки слушателя"""
    list_display = ('full_name', 'program', 'batch', 'email', 'phone', 'status', 'created_at')
    list_filter = ('status', 'created_at', 'program')
    search_fields = ('full_name', 'email', 'phone', 'comment')
    raw_id_fields = ('program', 'batch')
    ordering = ('-created_at',)

    fieldsets = (
        ('Данные слушателя', {
            'fields': ('full_name', 'email', 'phone', 'comment')
        }),
        ('Программа и поток', {
            'fields': ('program', 'batch')
        }),
        ('Обработка заявки', {
            'fields': ('status', 'admin_comment')
        }),
        ('Дополнительно', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ('created_at',)


@admin.register(CallbackRequest)
class CallbackRequestAdmin(admin.ModelAdmin):
    """Админка для запроса обратного звонка"""
    list_display = ('name', 'phone', 'email', 'created_at')
    search_fields = ('name', 'email', 'phone')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)
