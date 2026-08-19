from django.db.models import Q

from .models import Project


ADMIN_ROLES = {"admin", "superadmin"}


def user_role(user):
    """Return the normalized role while old portal accounts are migrated gradually."""
    if not getattr(user, "is_authenticated", False):
        return ""
    try:
        return user.organization.role.code.lower()
    except Exception:
        return (getattr(user, "role", "") or "").lower()


def projects_for_user(user):
    role = user_role(user)
    queryset = Project.objects.select_related("company", "client")
    if role in ADMIN_ROLES:
        try:
            return queryset.filter(company=user.organization.company)
        except (AttributeError, user.__class__.organization.RelatedObjectDoesNotExist):
            return queryset
    try:
        employee = user.organization.employee
    except (AttributeError, user.__class__.organization.RelatedObjectDoesNotExist):
        return queryset.none()
    return queryset.filter(members__employee=employee, members__is_active=True).distinct()


def project_for_user(user, project_id):
    return projects_for_user(user).get(pk=project_id)


def organization_for_user(user):
    """Return UserOrganization for user, or None if not linked."""
    try:
        return user.organization
    except (AttributeError, user.__class__.organization.RelatedObjectDoesNotExist):
        return None


def company_for_user(user):
    organization = organization_for_user(user)
    return organization.company if organization else None


def may_manage_master(user):
    return user_role(user) in ADMIN_ROLES


def may_approve(user):
    return user_role(user) in ADMIN_ROLES


def may_submit_field_work(user):
    return user_role(user) in {"mandor", "lapangan", "karyawan"}
