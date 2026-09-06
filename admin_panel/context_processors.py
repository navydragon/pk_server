"""Контекст-процессор для прав доступа в шаблонах admin_panel."""

from .permissions import (
    can_access_catalog,
    can_access_content,
    can_access_crm,
    can_delete_crm,
    can_export_crm,
    get_staff_role,
)


def staff_permissions(request):
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return {
            'staff_role': None,
            'can_access_catalog': False,
            'can_access_crm': False,
            'can_access_content': False,
            'can_delete_crm': False,
            'can_export_crm': False,
        }

    return {
        'staff_role': get_staff_role(user),
        'can_access_catalog': can_access_catalog(user),
        'can_access_crm': can_access_crm(user),
        'can_access_content': can_access_content(user),
        'can_delete_crm': can_delete_crm(user),
        'can_export_crm': can_export_crm(user),
    }
