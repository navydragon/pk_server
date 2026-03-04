from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy

# Namespace для URL
URL_NAMESPACE = 'admin_panel'
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from core.models import Application, CallbackRequest, CourseBatch, Direction, LearningFormat, Program
from publications.models import Case, Publication, Testimonial

from .forms import (
    ApplicationForm,
    CallbackRequestForm,
    CourseBatchForm,
    DirectionForm,
    LearningFormatForm,
    ProgramForm,
    PublicationForm,
    CaseForm,
    TestimonialForm,
)


# Авторизация
class CustomLoginView(LoginView):
    template_name = 'admin/login.html'
    redirect_authenticated_user = True

    def form_valid(self, form):
        messages.success(self.request, f'Добро пожаловать, {form.get_user().username}!')
        return super().form_valid(form)


class CustomLogoutView(LogoutView):
    next_page = 'admin_panel:login'
    
    def dispatch(self, request, *args, **kwargs):
        messages.info(request, 'Вы вышли из системы.')
        return super().dispatch(request, *args, **kwargs)


@login_required
def dashboard_view(request):
    """Главная страница админ-панели"""
    context = {
        'directions_count': Direction.objects.count(),
        'learning_formats_count': LearningFormat.objects.count(),
        'programs_count': Program.objects.count(),
        'course_batches_count': CourseBatch.objects.count(),
        'applications_count': Application.objects.count(),
        'callback_requests_count': CallbackRequest.objects.count(),
        'publications_count': Publication.objects.count(),
        'cases_count': Case.objects.count(),
        'testimonials_count': Testimonial.objects.count(),
    }
    return render(request, 'admin/dashboard.html', context)


# Direction Views
@method_decorator(login_required, name='dispatch')
class DirectionListView(ListView):
    model = Direction
    template_name = 'admin/direction_list.html'
    context_object_name = 'directions'
    paginate_by = None  # DataTables будет обрабатывать пагинацию на клиенте


@method_decorator(login_required, name='dispatch')
class DirectionCreateView(CreateView):
    model = Direction
    form_class = DirectionForm
    template_name = 'admin/direction_form.html'
    success_url = reverse_lazy('admin_panel:direction_list')

    def form_valid(self, form):
        messages.success(self.request, 'Направление успешно создано.')
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class DirectionUpdateView(UpdateView):
    model = Direction
    form_class = DirectionForm
    template_name = 'admin/direction_form.html'
    success_url = reverse_lazy('admin_panel:direction_list')

    def form_valid(self, form):
        messages.success(self.request, 'Направление успешно обновлено.')
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class DirectionDeleteView(DeleteView):
    model = Direction
    template_name = 'admin/direction_confirm_delete.html'
    success_url = reverse_lazy('admin_panel:direction_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Направление успешно удалено.')
        return super().delete(request, *args, **kwargs)


# LearningFormat Views
@method_decorator(login_required, name='dispatch')
class LearningFormatListView(ListView):
    model = LearningFormat
    template_name = 'admin/learningformat_list.html'
    context_object_name = 'formats'
    paginate_by = None  # DataTables будет обрабатывать пагинацию на клиенте


@method_decorator(login_required, name='dispatch')
class LearningFormatCreateView(CreateView):
    model = LearningFormat
    form_class = LearningFormatForm
    template_name = 'admin/learningformat_form.html'
    success_url = reverse_lazy('admin_panel:learningformat_list')

    def form_valid(self, form):
        messages.success(self.request, 'Форма обучения успешно создана.')
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class LearningFormatUpdateView(UpdateView):
    model = LearningFormat
    form_class = LearningFormatForm
    template_name = 'admin/learningformat_form.html'
    success_url = reverse_lazy('admin_panel:learningformat_list')

    def form_valid(self, form):
        messages.success(self.request, 'Форма обучения успешно обновлена.')
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class LearningFormatDeleteView(DeleteView):
    model = LearningFormat
    template_name = 'admin/learningformat_confirm_delete.html'
    success_url = reverse_lazy('admin_panel:learningformat_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Форма обучения успешно удалена.')
        return super().delete(request, *args, **kwargs)


# Program Views
@method_decorator(login_required, name='dispatch')
class ProgramListView(ListView):
    model = Program
    template_name = 'admin/program_list.html'
    context_object_name = 'programs'
    paginate_by = None  # DataTables будет обрабатывать пагинацию на клиенте

    def get_queryset(self):
        return Program.objects.select_related('direction', 'learning_format')


@method_decorator(login_required, name='dispatch')
class ProgramCreateView(CreateView):
    model = Program
    form_class = ProgramForm
    template_name = 'admin/program_form.html'
    success_url = reverse_lazy('admin_panel:program_list')

    def form_valid(self, form):
        messages.success(self.request, 'Программа успешно создана.')
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class ProgramUpdateView(UpdateView):
    model = Program
    form_class = ProgramForm
    template_name = 'admin/program_form.html'
    success_url = reverse_lazy('admin_panel:program_list')

    def form_valid(self, form):
        messages.success(self.request, 'Программа успешно обновлена.')
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class ProgramDeleteView(DeleteView):
    model = Program
    template_name = 'admin/program_confirm_delete.html'
    success_url = reverse_lazy('admin_panel:program_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Программа успешно удалена.')
        return super().delete(request, *args, **kwargs)


# CourseBatch Views
@method_decorator(login_required, name='dispatch')
class CourseBatchListView(ListView):
    model = CourseBatch
    template_name = 'admin/coursebatch_list.html'
    context_object_name = 'batches'
    paginate_by = None  # DataTables будет обрабатывать пагинацию на клиенте

    def get_queryset(self):
        return CourseBatch.objects.select_related('program', 'learning_format')


@method_decorator(login_required, name='dispatch')
class CourseBatchCreateView(CreateView):
    model = CourseBatch
    form_class = CourseBatchForm
    template_name = 'admin/coursebatch_form.html'
    success_url = reverse_lazy('admin_panel:coursebatch_list')

    def form_valid(self, form):
        messages.success(self.request, 'Поток/набор успешно создан.')
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class CourseBatchUpdateView(UpdateView):
    model = CourseBatch
    form_class = CourseBatchForm
    template_name = 'admin/coursebatch_form.html'
    success_url = reverse_lazy('admin_panel:coursebatch_list')

    def form_valid(self, form):
        messages.success(self.request, 'Поток/набор успешно обновлен.')
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class CourseBatchDeleteView(DeleteView):
    model = CourseBatch
    template_name = 'admin/coursebatch_confirm_delete.html'
    success_url = reverse_lazy('admin_panel:coursebatch_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Поток/набор успешно удален.')
        return super().delete(request, *args, **kwargs)


# Application Views
@method_decorator(login_required, name='dispatch')
class ApplicationListView(ListView):
    model = Application
    template_name = 'admin/application_list.html'
    context_object_name = 'applications'
    paginate_by = None  # DataTables будет обрабатывать пагинацию на клиенте

    def get_queryset(self):
        return Application.objects.select_related('program', 'batch')


@method_decorator(login_required, name='dispatch')
class ApplicationCreateView(CreateView):
    model = Application
    form_class = ApplicationForm
    template_name = 'admin/application_form.html'
    success_url = reverse_lazy('admin_panel:application_list')

    def form_valid(self, form):
        messages.success(self.request, 'Заявка успешно создана.')
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class ApplicationUpdateView(UpdateView):
    model = Application
    form_class = ApplicationForm
    template_name = 'admin/application_form.html'
    success_url = reverse_lazy('admin_panel:application_list')

    def form_valid(self, form):
        messages.success(self.request, 'Заявка успешно обновлена.')
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class ApplicationDeleteView(DeleteView):
    model = Application
    template_name = 'admin/application_confirm_delete.html'
    success_url = reverse_lazy('admin_panel:application_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Заявка успешно удалена.')
        return super().delete(request, *args, **kwargs)


# CallbackRequest Views
@method_decorator(login_required, name='dispatch')
class CallbackRequestListView(ListView):
    model = CallbackRequest
    template_name = 'admin/callbackrequest_list.html'
    context_object_name = 'callback_requests'
    paginate_by = None


@method_decorator(login_required, name='dispatch')
class CallbackRequestCreateView(CreateView):
    model = CallbackRequest
    form_class = CallbackRequestForm
    template_name = 'admin/callbackrequest_form.html'
    success_url = reverse_lazy('admin_panel:callbackrequest_list')

    def form_valid(self, form):
        messages.success(self.request, 'Запрос обратного звонка успешно создан.')
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class CallbackRequestUpdateView(UpdateView):
    model = CallbackRequest
    form_class = CallbackRequestForm
    template_name = 'admin/callbackrequest_form.html'
    success_url = reverse_lazy('admin_panel:callbackrequest_list')

    def form_valid(self, form):
        messages.success(self.request, 'Запрос обратного звонка успешно обновлён.')
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class CallbackRequestDeleteView(DeleteView):
    model = CallbackRequest
    template_name = 'admin/callbackrequest_confirm_delete.html'
    success_url = reverse_lazy('admin_panel:callbackrequest_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Запрос обратного звонка успешно удалён.')
        return super().delete(request, *args, **kwargs)


# Publication Views
@method_decorator(login_required, name='dispatch')
class PublicationListView(ListView):
    model = Publication
    template_name = 'admin/publication_list.html'
    context_object_name = 'publications'
    paginate_by = None

    def get_queryset(self):
        return Publication.objects.prefetch_related('categories', 'tags').order_by('-updated_at')


@method_decorator(login_required, name='dispatch')
class PublicationCreateView(CreateView):
    model = Publication
    form_class = PublicationForm
    template_name = 'admin/publication_form.html'
    success_url = reverse_lazy('admin_panel:publication_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        if not form.instance.slug and form.instance.title:
            import uuid
            from django.utils.text import slugify
            from publications.models import Publication
            base = slugify(form.instance.title)[:50] or f'pub-{uuid.uuid4().hex[:8]}'
            form.instance.slug = Publication.generate_unique_slug(base)
        messages.success(self.request, 'Публикация успешно создана.')
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class PublicationUpdateView(UpdateView):
    model = Publication
    form_class = PublicationForm
    template_name = 'admin/publication_form.html'
    success_url = reverse_lazy('admin_panel:publication_list')

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, 'Публикация успешно обновлена.')
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class PublicationDeleteView(DeleteView):
    model = Publication
    template_name = 'admin/publication_confirm_delete.html'
    success_url = reverse_lazy('admin_panel:publication_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Публикация успешно удалена.')
        return super().delete(request, *args, **kwargs)


# Case Views
@method_decorator(login_required, name='dispatch')
class CaseListView(ListView):
    model = Case
    template_name = 'admin/case_list.html'
    context_object_name = 'cases'
    paginate_by = None

    def get_queryset(self):
        return Case.objects.select_related('created_by').prefetch_related('categories', 'tags').order_by('-published_at')


@method_decorator(login_required, name='dispatch')
class CaseCreateView(CreateView):
    model = Case
    form_class = CaseForm
    template_name = 'admin/case_form.html'
    success_url = reverse_lazy('admin_panel:case_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        messages.success(self.request, 'Кейс успешно создан.')
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class CaseUpdateView(UpdateView):
    model = Case
    form_class = CaseForm
    template_name = 'admin/case_form.html'
    success_url = reverse_lazy('admin_panel:case_list')

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, 'Кейс успешно обновлён.')
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class CaseDeleteView(DeleteView):
    model = Case
    template_name = 'admin/case_confirm_delete.html'
    success_url = reverse_lazy('admin_panel:case_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Кейс успешно удалён.')
        return super().delete(request, *args, **kwargs)


# Testimonial Views
@method_decorator(login_required, name='dispatch')
class TestimonialListView(ListView):
    model = Testimonial
    template_name = 'admin/testimonial_list.html'
    context_object_name = 'testimonials'
    paginate_by = None

    def get_queryset(self):
        return Testimonial.objects.select_related('created_by').order_by('-created_at')


@method_decorator(login_required, name='dispatch')
class TestimonialCreateView(CreateView):
    model = Testimonial
    form_class = TestimonialForm
    template_name = 'admin/testimonial_form.html'
    success_url = reverse_lazy('admin_panel:testimonial_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        messages.success(self.request, 'Отзыв успешно создан.')
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class TestimonialUpdateView(UpdateView):
    model = Testimonial
    form_class = TestimonialForm
    template_name = 'admin/testimonial_form.html'
    success_url = reverse_lazy('admin_panel:testimonial_list')

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, 'Отзыв успешно обновлён.')
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class TestimonialDeleteView(DeleteView):
    model = Testimonial
    template_name = 'admin/testimonial_confirm_delete.html'
    success_url = reverse_lazy('admin_panel:testimonial_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Отзыв успешно удалён.')
        return super().delete(request, *args, **kwargs)
