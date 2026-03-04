from django.contrib import admin
from django.utils.text import slugify

from .models import Case, Category, Publication, Tag, Testimonial


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'sort_order', 'category_type')
    list_filter = ('category_type',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('sort_order', 'name')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Publication)
class PublicationAdmin(admin.ModelAdmin):
    list_display = ('title', 'type', 'status', 'published_at', 'is_featured', 'created_at')
    list_filter = ('type', 'status', 'is_featured')
    search_fields = ('title', 'short_description')
    filter_horizontal = ('categories', 'tags')
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')
    date_hierarchy = 'published_at'

    fieldsets = (
        ('Основное', {
            'fields': ('type', 'title', 'slug', 'status', 'published_at', 'is_featured', 'sort_order')
        }),
        ('Содержимое', {
            'fields': ('short_description', 'content', 'main_image')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('Категории и теги', {
            'fields': ('categories', 'tags'),
            'classes': ('collapse',)
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        if not obj.slug:
            base = slugify(obj.title) or 'pub'
            obj.slug = Publication.generate_unique_slug(base)
        super().save_model(request, obj, form, change)


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = ('title', 'client_company', 'status', 'published_at', 'is_featured')
    list_filter = ('status', 'is_featured', 'client_industry')
    search_fields = ('title', 'client_company', 'short_description', 'results_short')
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')
    filter_horizontal = ('categories', 'tags')
    date_hierarchy = 'published_at'

    fieldsets = (
        ('Основное', {
            'fields': ('title', 'slug', 'status', 'published_at', 'is_featured', 'sort_order')
        }),
        ('Клиент', {
            'fields': ('client_company', 'client_industry')
        }),
        ('Содержимое', {
            'fields': ('short_description', 'content', 'services', 'results_short', 'results_detailed', 'metrics', 'main_image')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('Категории и теги', {
            'fields': ('categories', 'tags'),
            'classes': ('collapse',)
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        if not obj.slug:
            base = slugify(obj.title) or 'case'
            # Используем общий генератор из Publication для единообразия
            obj.slug = Publication.generate_unique_slug(base)
        super().save_model(request, obj, form, change)


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('person_name', 'company_name', 'status', 'is_featured', 'created_at')
    list_filter = ('status', 'is_featured')
    search_fields = ('person_name', 'company_name', 'quote')
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')

    fieldsets = (
        ('Основное', {
            'fields': ('person_name', 'person_position', 'company_name', 'slug', 'status', 'published_at', 'is_featured', 'sort_order')
        }),
        ('Содержимое', {
            'fields': ('quote', 'rating', 'company_logo')
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        if not obj.slug:
            base = slugify(obj.person_name or 'testimonial') or 'testimonial'
            obj.slug = Publication.generate_unique_slug(base)
        super().save_model(request, obj, form, change)

