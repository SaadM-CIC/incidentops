from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied


class RoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin de base pour restreindre une vue à un ou plusieurs rôles.
    Usage : définir allowed_roles dans la vue.
    """
    allowed_roles = []

    def test_func(self):
        return self.request.user.role in self.allowed_roles

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        raise PermissionDenied


class TechnicienRequiredMixin(RoleRequiredMixin):
    allowed_roles = ['technicien', 'admin']


class AdminRequiredMixin(RoleRequiredMixin):
    allowed_roles = ['admin']
