"""Роли и права доступа для admin_panel."""

from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied

from core.choices import StaffRole


CONTENT_SECTIONS = frozenset({'publications', 'cases', 'testimonials'})
CATALOG_SECTIONS = frozenset({
    'directions', 'formats', 'programs', 'batches',
})
CRM_SECTIONS = frozenset({
    'applications', 'callback_requests', 'corporate_requests',
})


def get_staff_role(user):
    """
    Возвращает роль сотрудника или None.

    Суперпользователь без профиля считается администратором.
    Неактивный профиль = нет доступа.
    """
    if not user or not user.is_authenticated:
        return None

    try:
        profile = user.staff_profile
    except ObjectDoesNotExist:
        profile = None

    if profile is not None:
        if not profile.is_active:
            return None
        return profile.role

    if user.is_superuser:
        return StaffRole.ADMINISTRATOR

    return None


def is_administrator(user):
    return get_staff_role(user) == StaffRole.ADMINISTRATOR


def is_methodist(user):
    return get_staff_role(user) == StaffRole.METHODIST


def is_editor(user):
    return get_staff_role(user) == StaffRole.EDITOR


def can_access_admin_panel(user):
    return get_staff_role(user) is not None


def can_access_catalog(user):
    role = get_staff_role(user)
    return role in (StaffRole.ADMINISTRATOR, StaffRole.METHODIST)


def can_access_crm(user):
    role = get_staff_role(user)
    return role in (StaffRole.ADMINISTRATOR, StaffRole.METHODIST)


def can_access_content(user):
    return get_staff_role(user) is not None


def can_delete_crm(user):
    return is_administrator(user)


def can_export_crm(user):
    return can_access_crm(user)


def can_access_section(user, section):
    if section == 'analytics':
        return can_access_admin_panel(user)
    if section in CONTENT_SECTIONS:
        return can_access_content(user)
    if section in CATALOG_SECTIONS:
        return can_access_catalog(user)
    if section in CRM_SECTIONS:
        return can_access_crm(user)
    return can_access_admin_panel(user)


def staff_login_required(view_func):
    """Требует вход и наличие роли сотрудника."""

    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if not can_access_admin_panel(request.user):
            raise PermissionDenied('Нет доступа к административной панели.')
        return view_func(request, *args, **kwargs)

    return _wrapped


class StaffRequiredMixin:
    """Mixin для CBV: вход + роль сотрудника."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if not can_access_admin_panel(request.user):
            raise PermissionDenied('Нет доступа к административной панели.')
        if not self.has_section_access(request.user):
            raise PermissionDenied('Недостаточно прав для этого раздела.')
        return super().dispatch(request, *args, **kwargs)

    def has_section_access(self, user):
        return True


class CatalogAccessMixin(StaffRequiredMixin):
    """Доступ к каталогу: администратор и методист."""

    def has_section_access(self, user):
        return can_access_catalog(user)


class CRMAccessMixin(StaffRequiredMixin):
    """Доступ к CRM-обращениям: администратор и методист."""

    def has_section_access(self, user):
        return can_access_crm(user)


class ContentAccessMixin(StaffRequiredMixin):
    """Доступ к контенту: все роли сотрудников."""

    def has_section_access(self, user):
        return can_access_content(user)


class CRMDeleteMixin(CRMAccessMixin):
    """Удаление обращений — только администратор."""

    def has_section_access(self, user):
        return can_delete_crm(user)
