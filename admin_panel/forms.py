from django import forms

from core.models import Application, CallbackRequest, CourseBatch, Direction, LearningFormat, Program
from publications.models import Case, Publication, Testimonial
from publications.models import Publication


class DirectionForm(forms.ModelForm):
    """Форма для Direction"""
    class Meta:
        model = Direction
        fields = ['name', 'short_description', 'sort_order', 'status']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'short_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'sort_order': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }


class LearningFormatForm(forms.ModelForm):
    """Форма для LearningFormat"""
    class Meta:
        model = LearningFormat
        fields = ['name', 'short_description', 'full_description', 'sort_order', 'status']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'short_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'full_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'sort_order': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }


class ProgramForm(forms.ModelForm):
    """Форма для Program"""
    class Meta:
        model = Program
        fields = [
            'name', 'direction', 'program_type', 'training_direction_code', 'lead', 'about_description', 'curriculum',
            'target_audience', 'enrollment_process', 'learning_format', 'learning_format_comment',
            'hours_volume', 'duration', 'cost', 'outcome', 'requirements',
            'learning_outcomes', 'status'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'direction': forms.Select(attrs={'class': 'form-select'}),
            'program_type': forms.Select(attrs={'class': 'form-select'}),
            'training_direction_code': forms.TextInput(attrs={'class': 'form-control'}),
            'lead': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'about_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'curriculum': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'target_audience': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'enrollment_process': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'learning_format': forms.Select(attrs={'class': 'form-select'}),
            'learning_format_comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'hours_volume': forms.NumberInput(attrs={'class': 'form-control'}),
            'duration': forms.TextInput(attrs={'class': 'form-control'}),
            'cost': forms.TextInput(attrs={'class': 'form-control'}),
            'outcome': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'requirements': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'learning_outcomes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }


class CourseBatchForm(forms.ModelForm):
    """Форма для CourseBatch"""
    start_date = forms.DateField(
        widget=forms.DateInput(
            format='%Y-%m-%d',
            attrs={'class': 'form-control', 'type': 'date'}
        ),
        input_formats=['%Y-%m-%d'],
        required=True
    )
    end_date = forms.DateField(
        widget=forms.DateInput(
            format='%Y-%m-%d',
            attrs={'class': 'form-control', 'type': 'date'}
        ),
        input_formats=['%Y-%m-%d'],
        required=False
    )
    
    class Meta:
        model = CourseBatch
        fields = [
            'program', 'name', 'start_date', 'end_date', 'learning_format',
            'schedule', 'seats_count', 'cost', 'status'
        ]
        widgets = {
            'program': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'learning_format': forms.Select(attrs={'class': 'form-select'}),
            'schedule': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'seats_count': forms.NumberInput(attrs={'class': 'form-control'}),
            'cost': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and end_date < start_date:
            raise forms.ValidationError({
                'end_date': 'Дата окончания не может быть раньше даты начала.'
            })
        
        return cleaned_data


class ApplicationForm(forms.ModelForm):
    """Форма для Application (заявка слушателя)"""
    class Meta:
        model = Application
        fields = [
            'full_name', 'program', 'batch', 'email', 'phone',
            'comment', 'status', 'admin_comment'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'program': forms.Select(attrs={'class': 'form-select'}),
            'batch': forms.Select(attrs={'class': 'form-select'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'admin_comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'program' in self.data:
            try:
                program_id = int(self.data.get('program'))
                self.fields['batch'].queryset = CourseBatch.objects.filter(
                    program_id=program_id
                ).order_by('-start_date')
            except (ValueError, TypeError):
                pass
        elif self.instance and self.instance.pk:
            self.fields['batch'].queryset = self.instance.program.batches.order_by(
                '-start_date'
            )
        else:
            self.fields['batch'].queryset = CourseBatch.objects.none()

    def clean(self):
        cleaned_data = super().clean()
        program = cleaned_data.get('program')
        batch = cleaned_data.get('batch')

        if program and batch and batch.program_id != program.id:
            raise forms.ValidationError({
                'batch': 'Выбранный поток не относится к выбранной программе.'
            })

        return cleaned_data


class CallbackRequestForm(forms.ModelForm):
    """Форма для CallbackRequest (запрос обратного звонка)."""
    class Meta:
        model = CallbackRequest
        fields = ['name', 'phone', 'email']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }


class PublicationForm(forms.ModelForm):
    """Форма для Publication (новость или статья)."""
    published_at = forms.DateTimeField(
        widget=forms.DateTimeInput(
            format='%Y-%m-%dT%H:%M',
            attrs={'class': 'form-control', 'type': 'datetime-local'}
        ),
        input_formats=['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M', '%Y-%m-%d'],
        required=False
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.published_at:
            from django.utils import timezone
            dt = self.instance.published_at
            if timezone.is_aware(dt):
                dt = timezone.localtime(dt)
            self.initial['published_at'] = dt.strftime('%Y-%m-%dT%H:%M')

    class Meta:
        model = Publication
        fields = [
            'type', 'title', 'slug', 'short_description', 'content',
            'status', 'published_at', 'main_image', 'is_featured', 'sort_order',
            'meta_title', 'meta_description',
            'categories', 'tags',
        ]
        widgets = {
            'type': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
            'short_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 8}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'main_image': forms.FileInput(attrs={'class': 'form-control'}),
            'company_logo': forms.FileInput(attrs={'class': 'form-control'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'sort_order': forms.NumberInput(attrs={'class': 'form-control'}),
            'meta_title': forms.TextInput(attrs={'class': 'form-control'}),
            'meta_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'categories': forms.SelectMultiple(attrs={'class': 'form-select'}),
            'tags': forms.SelectMultiple(attrs={'class': 'form-select'}),
        }


class CaseForm(forms.ModelForm):
    """Форма для Case."""

    published_at = forms.DateTimeField(
        widget=forms.DateTimeInput(
            format='%Y-%m-%dT%H:%M',
            attrs={'class': 'form-control', 'type': 'datetime-local'},
        ),
        input_formats=['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M', '%Y-%m-%d'],
        required=False,
    )

    class Meta:
        model = Case
        fields = [
            'title',
            'slug',
            'short_description',
            'content',
            'client_company',
            'client_industry',
            'services',
            'results_short',
            'results_detailed',
            'metrics',
            'main_image',
            'status',
            'published_at',
            'is_featured',
            'sort_order',
            'meta_title',
            'meta_description',
            'categories',
            'tags',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
            'short_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 8}),
            'client_company': forms.TextInput(attrs={'class': 'form-control'}),
            'client_industry': forms.TextInput(attrs={'class': 'form-control'}),
            'services': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'results_short': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'results_detailed': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'metrics': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'main_image': forms.FileInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'sort_order': forms.NumberInput(attrs={'class': 'form-control'}),
            'meta_title': forms.TextInput(attrs={'class': 'form-control'}),
            'meta_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'categories': forms.SelectMultiple(attrs={'class': 'form-select'}),
            'tags': forms.SelectMultiple(attrs={'class': 'form-select'}),
        }


class TestimonialForm(forms.ModelForm):
    """Форма для Testimonial."""

    published_at = forms.DateTimeField(
        widget=forms.DateTimeInput(
            format='%Y-%m-%dT%H:%M',
            attrs={'class': 'form-control', 'type': 'datetime-local'},
        ),
        input_formats=['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M', '%Y-%m-%d'],
        required=False,
    )

    class Meta:
        model = Testimonial
        fields = [
            'person_name',
            'person_position',
            'company_name',
            'quote',
            'rating',
            'company_logo',
            'slug',
            'status',
            'published_at',
            'is_featured',
            'sort_order',
        ]
        widgets = {
            'person_name': forms.TextInput(attrs={'class': 'form-control'}),
            'person_position': forms.TextInput(attrs={'class': 'form-control'}),
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'quote': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'rating': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 5}),
            'company_logo': forms.FileInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'sort_order': forms.NumberInput(attrs={'class': 'form-control'}),
        }

