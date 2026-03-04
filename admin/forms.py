from django import forms

from core.models import CourseBatch, Direction, LearningFormat, Program


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
