from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, UpdateView

from .forms import RegisterForm, CustomAuthenticationForm, ProfileEditForm
from .models import CustomUser


class RegisterView(CreateView):
    model = CustomUser
    form_class = RegisterForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('accounts:login')

    def form_valid(self, form):
        response = super().form_valid(form)
        # Connecte automatiquement l'utilisateur après inscription
        login(self.request, self.object)
        return response

    def get_success_url(self):
        return reverse_lazy('accounts:profile')


class CustomLoginView(LoginView):
    form_class = CustomAuthenticationForm
    template_name = 'accounts/login.html'

    def get_success_url(self):
        return reverse_lazy('accounts:profile')


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('accounts:login')


class ProfileView(LoginRequiredMixin, DetailView):
    model = CustomUser
    template_name = 'accounts/profile.html'
    context_object_name = 'profile_user'

    def get_object(self):
        return self.request.user


class ProfileEditView(LoginRequiredMixin, UpdateView):
    model = CustomUser
    form_class = ProfileEditForm
    template_name = 'accounts/profile_edit.html'
    success_url = reverse_lazy('accounts:profile')

    def get_object(self):
        return self.request.user