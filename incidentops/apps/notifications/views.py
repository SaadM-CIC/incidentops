from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from django.views import View
from django.shortcuts import redirect
from .models import Notification


class NotificationListView(LoginRequiredMixin, ListView):
    model = Notification
    template_name = 'notifications/list.html'
    context_object_name = 'notifications'

    def get_queryset(self):
        qs = Notification.objects.filter(recipient=self.request.user)
        # Marque toutes comme lues à l'ouverture de la page
        qs.filter(is_read=False).update(is_read=True)
        return qs


class NotificationMarkReadView(LoginRequiredMixin, View):
    def post(self, request, pk):
        Notification.objects.filter(pk=pk, recipient=request.user).update(is_read=True)
        return redirect('notifications:list')