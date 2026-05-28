from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.views import View

from apps.tickets.models import Ticket
from .forms import CommentForm
from .models import Comment


class CommentCreateView(LoginRequiredMixin, View):

    def post(self, request, ticket_pk):
        ticket = get_object_or_404(Ticket, pk=ticket_pk)
        user = request.user

        # Vérifier que l'utilisateur a accès à ce ticket
        if user.role == 'user' and ticket.created_by != user:
            raise PermissionDenied

        form = CommentForm(request.POST, user=user)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.ticket = ticket
            comment.author = user
            comment.save()
            messages.success(request, "Commentaire ajouté.")
        else:
            messages.error(request, "Erreur dans le formulaire.")

        return redirect('tickets:detail', pk=ticket_pk)


class CommentDeleteView(LoginRequiredMixin, View):

    def post(self, request, pk):
        comment = get_object_or_404(Comment, pk=pk)

        # Seul l'auteur ou un admin peut supprimer
        if comment.author != request.user and request.user.role != 'admin':
            raise PermissionDenied

        ticket_pk = comment.ticket.pk
        comment.delete()
        messages.success(request, "Commentaire supprimé.")
        return redirect('tickets:detail', pk=ticket_pk)