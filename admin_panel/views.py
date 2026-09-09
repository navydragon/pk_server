from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from core.choices import (
    ApplicationStatus,
    CallbackRequestStatus,
    CorporateRequestStatus,
)
from core.models import (
    Application,
    CallbackRequest,
    CorporateRequest,
    CourseBatch,
    Direction,
    LearningFormat,
    Program,
)
from core.settings_service import SHOW_TEST_DATA, get_bool_setting, set_setting
from publications.models import Case, Publication, Testimonial

from .analytics import build_analytics
from .crm_utils import apply_common_crm_filters, csv_response
from .forms import (
    ApplicationForm,
    CallbackRequestForm,
    CaseForm,
    CorporateRequestForm,
    CourseBatchForm,
    DirectionForm,
    LearningFormatForm,
    ProgramForm,
    PublicationForm,
    SettingsForm,
    TestimonialForm,
)
from .permissions import (
    CRMAccessMixin,
    CRMDeleteMixin,
    CatalogAccessMixin,
    ContentAccessMixin,
    SettingsAccessMixin,
    can_access_catalog,
    can_access_content,
    can_access_crm,
    can_delete_crm,
    can_export_crm,
    staff_login_required,
)

User = get_user_model()
URL_NAMESPACE = 'admin_panel'


# Авторизация
class CustomLoginView(LoginView):
    template_name = 'admin/login.html'
    redirect_authenticated_user = True

    def form_valid(self, form):
        user = form.get_user()
        messages.success(self.request, f'Добро пожаловать, {user.username}!')
        profile = getattr(user, 'staff_profile', None)
        if profile is not None:
            profile.last_login_at = timezone.now()
            profile.save(update_fields=['last_login_at'])
        return super().form_valid(form)


class CustomLogoutView(LogoutView):
    next_page = 'admin_panel:login'

    def dispatch(self, request, *args, **kwargs):
        messages.info(request, 'Вы вышли из системы.')
        return super().dispatch(request, *args, **kwargs)


@staff_login_required
def dashboard_view(request):
    """Главная страница админ-панели"""
    context = {
        'directions_count': Direction.objects.count(),
        'learning_formats_count': LearningFormat.objects.count(),
        'programs_count': Program.objects.count(),
        'course_batches_count': CourseBatch.objects.count(),
        'applications_count': Application.objects.count(),
        'applications_new_count': Application.objects.filter(
            status=ApplicationStatus.NEW
        ).count(),
        'corporate_requests_count': CorporateRequest.objects.count(),
        'corporate_requests_new_count': CorporateRequest.objects.filter(
            status=CorporateRequestStatus.NEW
        ).count(),
        'callback_requests_count': CallbackRequest.objects.count(),
        'callback_requests_new_count': CallbackRequest.objects.filter(
            status=CallbackRequestStatus.NEW
        ).count(),
        'publications_count': Publication.objects.count(),
        'cases_count': Case.objects.count(),
        'testimonials_count': Testimonial.objects.count(),
        'can_access_crm': can_access_crm(request.user),
    }
    return render(request, 'admin/dashboard.html', context)


@staff_login_required
def analytics_view(request):
    """Страница базовой аналитики."""
    import json

    include_crm = can_access_crm(request.user)
    include_catalog = can_access_catalog(request.user)
    include_content = can_access_content(request.user)

    context = build_analytics(
        request.GET,
        include_crm=include_crm,
        include_catalog=include_catalog,
        include_content=include_content,
    )
    context['chart_data_json'] = json.dumps(
        context.get('chart_json') or {},
        ensure_ascii=False,
    )
    return render(request, 'admin/analytics.html', context)


class SettingsView(SettingsAccessMixin, View):
    """Системные настройки (только администратор)."""

    template_name = 'admin/settings.html'

    def get(self, request):
        form = SettingsForm(
            initial={'show_test_data': get_bool_setting(SHOW_TEST_DATA, default=False)}
        )
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = SettingsForm(request.POST)
        if form.is_valid():
            value = 'true' if form.cleaned_data['show_test_data'] else 'false'
            set_setting(SHOW_TEST_DATA, value)
            messages.success(request, 'Настройки сохранены.')
            return redirect('admin_panel:settings')
        return render(request, self.template_name, {'form': form})


def _assignees_context():
    return User.objects.filter(is_active=True).order_by('username')


# Direction Views
class DirectionListView(CatalogAccessMixin, ListView):
    model = Direction
    template_name = 'admin/direction_list.html'
    context_object_name = 'directions'
    paginate_by = None


class DirectionCreateView(CatalogAccessMixin, CreateView):
    model = Direction
    form_class = DirectionForm
    template_name = 'admin/direction_form.html'
    success_url = reverse_lazy('admin_panel:direction_list')

    def form_valid(self, form):
        messages.success(self.request, 'Направление успешно создано.')
        return super().form_valid(form)


class DirectionUpdateView(CatalogAccessMixin, UpdateView):
    model = Direction
    form_class = DirectionForm
    template_name = 'admin/direction_form.html'
    success_url = reverse_lazy('admin_panel:direction_list')

    def form_valid(self, form):
        messages.success(self.request, 'Направление успешно обновлено.')
        return super().form_valid(form)


class DirectionDeleteView(CatalogAccessMixin, DeleteView):
    model = Direction
    template_name = 'admin/direction_confirm_delete.html'
    success_url = reverse_lazy('admin_panel:direction_list')

    def form_valid(self, form):
        messages.success(self.request, 'Направление успешно удалено.')
        return super().form_valid(form)


# LearningFormat Views
class LearningFormatListView(CatalogAccessMixin, ListView):
    model = LearningFormat
    template_name = 'admin/learningformat_list.html'
    context_object_name = 'formats'
    paginate_by = None


class LearningFormatCreateView(CatalogAccessMixin, CreateView):
    model = LearningFormat
    form_class = LearningFormatForm
    template_name = 'admin/learningformat_form.html'
    success_url = reverse_lazy('admin_panel:learningformat_list')

    def form_valid(self, form):
        messages.success(self.request, 'Форма обучения успешно создана.')
        return super().form_valid(form)


class LearningFormatUpdateView(CatalogAccessMixin, UpdateView):
    model = LearningFormat
    form_class = LearningFormatForm
    template_name = 'admin/learningformat_form.html'
    success_url = reverse_lazy('admin_panel:learningformat_list')

    def form_valid(self, form):
        messages.success(self.request, 'Форма обучения успешно обновлена.')
        return super().form_valid(form)


class LearningFormatDeleteView(CatalogAccessMixin, DeleteView):
    model = LearningFormat
    template_name = 'admin/learningformat_confirm_delete.html'
    success_url = reverse_lazy('admin_panel:learningformat_list')

    def form_valid(self, form):
        messages.success(self.request, 'Форма обучения успешно удалена.')
        return super().form_valid(form)


# Program Views
class ProgramListView(CatalogAccessMixin, ListView):
    model = Program
    template_name = 'admin/program_list.html'
    context_object_name = 'programs'
    paginate_by = None

    def get_queryset(self):
        return Program.objects.select_related('direction', 'learning_format').order_by('position', 'name')


class ProgramCreateView(CatalogAccessMixin, CreateView):
    model = Program
    form_class = ProgramForm
    template_name = 'admin/program_form.html'
    success_url = reverse_lazy('admin_panel:program_list')

    def form_valid(self, form):
        messages.success(self.request, 'Программа успешно создана.')
        return super().form_valid(form)


class ProgramUpdateView(CatalogAccessMixin, UpdateView):
    model = Program
    form_class = ProgramForm
    template_name = 'admin/program_form.html'
    success_url = reverse_lazy('admin_panel:program_list')

    def form_valid(self, form):
        messages.success(self.request, 'Программа успешно обновлена.')
        return super().form_valid(form)


class ProgramDeleteView(CatalogAccessMixin, DeleteView):
    model = Program
    template_name = 'admin/program_confirm_delete.html'
    success_url = reverse_lazy('admin_panel:program_list')

    def form_valid(self, form):
        messages.success(self.request, 'Программа успешно удалена.')
        return super().form_valid(form)


# CourseBatch Views
class CourseBatchListView(CatalogAccessMixin, ListView):
    model = CourseBatch
    template_name = 'admin/coursebatch_list.html'
    context_object_name = 'batches'
    paginate_by = None

    def get_queryset(self):
        return CourseBatch.objects.select_related('program', 'learning_format')


class CourseBatchCreateView(CatalogAccessMixin, CreateView):
    model = CourseBatch
    form_class = CourseBatchForm
    template_name = 'admin/coursebatch_form.html'
    success_url = reverse_lazy('admin_panel:coursebatch_list')

    def form_valid(self, form):
        messages.success(self.request, 'Поток/набор успешно создан.')
        return super().form_valid(form)


class CourseBatchUpdateView(CatalogAccessMixin, UpdateView):
    model = CourseBatch
    form_class = CourseBatchForm
    template_name = 'admin/coursebatch_form.html'
    success_url = reverse_lazy('admin_panel:coursebatch_list')

    def form_valid(self, form):
        messages.success(self.request, 'Поток/набор успешно обновлен.')
        return super().form_valid(form)


class CourseBatchDeleteView(CatalogAccessMixin, DeleteView):
    model = CourseBatch
    template_name = 'admin/coursebatch_confirm_delete.html'
    success_url = reverse_lazy('admin_panel:coursebatch_list')

    def form_valid(self, form):
        messages.success(self.request, 'Поток/набор успешно удален.')
        return super().form_valid(form)


# --- CRM: Applications ---

def _filter_applications(queryset, params):
    queryset = apply_common_crm_filters(queryset, params)
    program = params.get('program')
    if program:
        try:
            queryset = queryset.filter(program_id=int(program))
        except (TypeError, ValueError):
            pass
    return queryset


class ApplicationListView(CRMAccessMixin, ListView):
    model = Application
    template_name = 'admin/application_list.html'
    context_object_name = 'applications'
    paginate_by = None

    def get_queryset(self):
        qs = Application.objects.select_related('program', 'batch', 'assigned_to')
        return _filter_applications(qs, self.request.GET)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = ApplicationStatus.CHOICES
        context['programs'] = Program.objects.order_by('name')
        context['assignees'] = _assignees_context()
        context['filters'] = self.request.GET
        context['can_delete_crm'] = can_delete_crm(self.request.user)
        context['can_export_crm'] = can_export_crm(self.request.user)
        return context


class ApplicationCreateView(CRMAccessMixin, CreateView):
    model = Application
    form_class = ApplicationForm
    template_name = 'admin/application_form.html'
    success_url = reverse_lazy('admin_panel:application_list')

    def form_valid(self, form):
        messages.success(self.request, 'Заявка успешно создана.')
        return super().form_valid(form)


class ApplicationUpdateView(CRMAccessMixin, UpdateView):
    model = Application
    form_class = ApplicationForm
    template_name = 'admin/application_form.html'
    success_url = reverse_lazy('admin_panel:application_list')

    def form_valid(self, form):
        messages.success(self.request, 'Заявка успешно обновлена.')
        return super().form_valid(form)


class ApplicationDeleteView(CRMDeleteMixin, DeleteView):
    model = Application
    template_name = 'admin/application_confirm_delete.html'
    success_url = reverse_lazy('admin_panel:application_list')

    def form_valid(self, form):
        messages.success(self.request, 'Заявка успешно удалена.')
        return super().form_valid(form)


class ApplicationExportView(CRMAccessMixin, View):
    def get(self, request, *args, **kwargs):
        if not can_export_crm(request.user):
            messages.error(request, 'Недостаточно прав для экспорта.')
            return redirect('admin_panel:application_list')

        qs = _filter_applications(
            Application.objects.select_related('program', 'batch', 'assigned_to'),
            request.GET,
        )
        rows = []
        for item in qs:
            rows.append([
                item.id,
                item.full_name,
                item.program.name,
                str(item.batch) if item.batch else '',
                item.email,
                item.phone,
                item.get_preferred_contact_display() if item.preferred_contact else '',
                item.get_status_display(),
                item.assigned_to.get_username() if item.assigned_to else '',
                item.comment,
                item.admin_comment,
                item.created_at.strftime('%d.%m.%Y %H:%M'),
            ])
        return csv_response(
            'applications.csv',
            [
                'ID', 'ФИО', 'Программа', 'Поток', 'Email', 'Телефон',
                'Способ связи', 'Статус', 'Ответственный', 'Комментарий',
                'Комментарий админа', 'Дата создания',
            ],
            rows,
        )


class ApplicationQuickStatusView(CRMAccessMixin, View):
    def post(self, request, pk, *args, **kwargs):
        application = get_object_or_404(Application, pk=pk)
        new_status = request.POST.get('status')
        valid = {c[0] for c in ApplicationStatus.CHOICES}
        if new_status in valid:
            application.status = new_status
            application.save(update_fields=['status', 'updated_at'])
            messages.success(request, 'Статус заявки обновлён.')
        else:
            messages.error(request, 'Некорректный статус.')
        return redirect(request.POST.get('next') or 'admin_panel:application_list')


# --- CRM: Corporate requests ---

def _filter_corporate_requests(queryset, params):
    queryset = apply_common_crm_filters(queryset, params)
    direction = params.get('direction')
    if direction:
        try:
            queryset = queryset.filter(directions__id=int(direction)).distinct()
        except (TypeError, ValueError):
            pass
    return queryset


class CorporateRequestListView(CRMAccessMixin, ListView):
    model = CorporateRequest
    template_name = 'admin/corporaterequest_list.html'
    context_object_name = 'corporate_requests'
    paginate_by = None

    def get_queryset(self):
        qs = CorporateRequest.objects.select_related('assigned_to').prefetch_related(
            'directions', 'programs'
        )
        return _filter_corporate_requests(qs, self.request.GET)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = CorporateRequestStatus.CHOICES
        context['directions'] = Direction.objects.order_by('name')
        context['assignees'] = _assignees_context()
        context['filters'] = self.request.GET
        context['can_delete_crm'] = can_delete_crm(self.request.user)
        context['can_export_crm'] = can_export_crm(self.request.user)
        return context


class CorporateRequestCreateView(CRMAccessMixin, CreateView):
    model = CorporateRequest
    form_class = CorporateRequestForm
    template_name = 'admin/corporaterequest_form.html'
    success_url = reverse_lazy('admin_panel:corporaterequest_list')

    def form_valid(self, form):
        messages.success(self.request, 'Корпоративный запрос успешно создан.')
        return super().form_valid(form)


class CorporateRequestUpdateView(CRMAccessMixin, UpdateView):
    model = CorporateRequest
    form_class = CorporateRequestForm
    template_name = 'admin/corporaterequest_form.html'
    success_url = reverse_lazy('admin_panel:corporaterequest_list')

    def form_valid(self, form):
        messages.success(self.request, 'Корпоративный запрос успешно обновлён.')
        return super().form_valid(form)


class CorporateRequestDeleteView(CRMDeleteMixin, DeleteView):
    model = CorporateRequest
    template_name = 'admin/corporaterequest_confirm_delete.html'
    success_url = reverse_lazy('admin_panel:corporaterequest_list')

    def form_valid(self, form):
        messages.success(self.request, 'Корпоративный запрос успешно удалён.')
        return super().form_valid(form)


class CorporateRequestExportView(CRMAccessMixin, View):
    def get(self, request, *args, **kwargs):
        if not can_export_crm(request.user):
            messages.error(request, 'Недостаточно прав для экспорта.')
            return redirect('admin_panel:corporaterequest_list')

        qs = _filter_corporate_requests(
            CorporateRequest.objects.select_related('assigned_to').prefetch_related(
                'directions', 'programs'
            ),
            request.GET,
        )
        rows = []
        for item in qs:
            rows.append([
                item.id,
                item.organization_name,
                item.contact_name,
                item.contact_position,
                item.phone,
                item.email,
                item.topics,
                ', '.join(d.name for d in item.directions.all()),
                item.employees_count,
                item.desired_dates,
                item.get_status_display(),
                item.assigned_to.get_username() if item.assigned_to else '',
                item.created_at.strftime('%d.%m.%Y %H:%M'),
            ])
        return csv_response(
            'corporate_requests.csv',
            [
                'ID', 'Организация', 'Контакт', 'Должность', 'Телефон', 'Email',
                'Темы', 'Направления', 'Сотрудников', 'Сроки', 'Статус',
                'Ответственный', 'Дата создания',
            ],
            rows,
        )


class CorporateRequestQuickStatusView(CRMAccessMixin, View):
    def post(self, request, pk, *args, **kwargs):
        obj = get_object_or_404(CorporateRequest, pk=pk)
        new_status = request.POST.get('status')
        valid = {c[0] for c in CorporateRequestStatus.CHOICES}
        if new_status in valid:
            obj.status = new_status
            obj.save(update_fields=['status', 'updated_at'])
            messages.success(request, 'Статус корпоративного запроса обновлён.')
        else:
            messages.error(request, 'Некорректный статус.')
        return redirect(request.POST.get('next') or 'admin_panel:corporaterequest_list')


# --- CRM: Callback requests ---

def _filter_callback_requests(queryset, params):
    return apply_common_crm_filters(queryset, params)


class CallbackRequestListView(CRMAccessMixin, ListView):
    model = CallbackRequest
    template_name = 'admin/callbackrequest_list.html'
    context_object_name = 'callback_requests'
    paginate_by = None

    def get_queryset(self):
        qs = CallbackRequest.objects.select_related('assigned_to')
        return _filter_callback_requests(qs, self.request.GET)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = CallbackRequestStatus.CHOICES
        context['assignees'] = _assignees_context()
        context['filters'] = self.request.GET
        context['can_delete_crm'] = can_delete_crm(self.request.user)
        context['can_export_crm'] = can_export_crm(self.request.user)
        return context


class CallbackRequestCreateView(CRMAccessMixin, CreateView):
    model = CallbackRequest
    form_class = CallbackRequestForm
    template_name = 'admin/callbackrequest_form.html'
    success_url = reverse_lazy('admin_panel:callbackrequest_list')

    def form_valid(self, form):
        messages.success(self.request, 'Запрос обратного звонка успешно создан.')
        return super().form_valid(form)


class CallbackRequestUpdateView(CRMAccessMixin, UpdateView):
    model = CallbackRequest
    form_class = CallbackRequestForm
    template_name = 'admin/callbackrequest_form.html'
    success_url = reverse_lazy('admin_panel:callbackrequest_list')

    def form_valid(self, form):
        messages.success(self.request, 'Запрос обратного звонка успешно обновлён.')
        return super().form_valid(form)


class CallbackRequestDeleteView(CRMDeleteMixin, DeleteView):
    model = CallbackRequest
    template_name = 'admin/callbackrequest_confirm_delete.html'
    success_url = reverse_lazy('admin_panel:callbackrequest_list')

    def form_valid(self, form):
        messages.success(self.request, 'Запрос обратного звонка успешно удалён.')
        return super().form_valid(form)


class CallbackRequestExportView(CRMAccessMixin, View):
    def get(self, request, *args, **kwargs):
        if not can_export_crm(request.user):
            messages.error(request, 'Недостаточно прав для экспорта.')
            return redirect('admin_panel:callbackrequest_list')

        qs = _filter_callback_requests(
            CallbackRequest.objects.select_related('assigned_to'),
            request.GET,
        )
        rows = []
        for item in qs:
            rows.append([
                item.id,
                item.name,
                item.phone,
                item.email,
                item.get_request_type_display() if item.request_type else '',
                item.comment,
                item.get_status_display(),
                item.assigned_to.get_username() if item.assigned_to else '',
                item.created_at.strftime('%d.%m.%Y %H:%M'),
            ])
        return csv_response(
            'callback_requests.csv',
            [
                'ID', 'Имя', 'Телефон', 'Email', 'Тип', 'Комментарий',
                'Статус', 'Ответственный', 'Дата создания',
            ],
            rows,
        )


class CallbackRequestQuickStatusView(CRMAccessMixin, View):
    def post(self, request, pk, *args, **kwargs):
        obj = get_object_or_404(CallbackRequest, pk=pk)
        new_status = request.POST.get('status')
        valid = {c[0] for c in CallbackRequestStatus.CHOICES}
        if new_status in valid:
            obj.status = new_status
            obj.save(update_fields=['status', 'updated_at'])
            messages.success(request, 'Статус запроса звонка обновлён.')
        else:
            messages.error(request, 'Некорректный статус.')
        return redirect(request.POST.get('next') or 'admin_panel:callbackrequest_list')


# Publication Views
class PublicationListView(ContentAccessMixin, ListView):
    model = Publication
    template_name = 'admin/publication_list.html'
    context_object_name = 'publications'
    paginate_by = None

    def get_queryset(self):
        return Publication.objects.prefetch_related('categories', 'tags').order_by('-updated_at')


class PublicationCreateView(ContentAccessMixin, CreateView):
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
            base = slugify(form.instance.title)[:50] or f'pub-{uuid.uuid4().hex[:8]}'
            form.instance.slug = Publication.generate_unique_slug(base)
        messages.success(self.request, 'Публикация успешно создана.')
        return super().form_valid(form)


class PublicationUpdateView(ContentAccessMixin, UpdateView):
    model = Publication
    form_class = PublicationForm
    template_name = 'admin/publication_form.html'
    success_url = reverse_lazy('admin_panel:publication_list')

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, 'Публикация успешно обновлена.')
        return super().form_valid(form)


class PublicationDeleteView(ContentAccessMixin, DeleteView):
    model = Publication
    template_name = 'admin/publication_confirm_delete.html'
    success_url = reverse_lazy('admin_panel:publication_list')

    def form_valid(self, form):
        messages.success(self.request, 'Публикация успешно удалена.')
        return super().form_valid(form)


# Case Views
class CaseListView(ContentAccessMixin, ListView):
    model = Case
    template_name = 'admin/case_list.html'
    context_object_name = 'cases'
    paginate_by = None

    def get_queryset(self):
        return Case.objects.select_related('created_by').prefetch_related(
            'categories', 'tags'
        ).order_by('-published_at')


class CaseCreateView(ContentAccessMixin, CreateView):
    model = Case
    form_class = CaseForm
    template_name = 'admin/case_form.html'
    success_url = reverse_lazy('admin_panel:case_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        messages.success(self.request, 'Кейс успешно создан.')
        return super().form_valid(form)


class CaseUpdateView(ContentAccessMixin, UpdateView):
    model = Case
    form_class = CaseForm
    template_name = 'admin/case_form.html'
    success_url = reverse_lazy('admin_panel:case_list')

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, 'Кейс успешно обновлён.')
        return super().form_valid(form)


class CaseDeleteView(ContentAccessMixin, DeleteView):
    model = Case
    template_name = 'admin/case_confirm_delete.html'
    success_url = reverse_lazy('admin_panel:case_list')

    def form_valid(self, form):
        messages.success(self.request, 'Кейс успешно удалён.')
        return super().form_valid(form)


# Testimonial Views
class TestimonialListView(ContentAccessMixin, ListView):
    model = Testimonial
    template_name = 'admin/testimonial_list.html'
    context_object_name = 'testimonials'
    paginate_by = None

    def get_queryset(self):
        return Testimonial.objects.select_related('created_by').order_by('-created_at')


class TestimonialCreateView(ContentAccessMixin, CreateView):
    model = Testimonial
    form_class = TestimonialForm
    template_name = 'admin/testimonial_form.html'
    success_url = reverse_lazy('admin_panel:testimonial_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        messages.success(self.request, 'Отзыв успешно создан.')
        return super().form_valid(form)


class TestimonialUpdateView(ContentAccessMixin, UpdateView):
    model = Testimonial
    form_class = TestimonialForm
    template_name = 'admin/testimonial_form.html'
    success_url = reverse_lazy('admin_panel:testimonial_list')

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, 'Отзыв успешно обновлён.')
        return super().form_valid(form)


class TestimonialDeleteView(ContentAccessMixin, DeleteView):
    model = Testimonial
    template_name = 'admin/testimonial_confirm_delete.html'
    success_url = reverse_lazy('admin_panel:testimonial_list')

    def form_valid(self, form):
        messages.success(self.request, 'Отзыв успешно удалён.')
        return super().form_valid(form)
