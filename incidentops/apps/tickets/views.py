from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail, EmailMultiAlternatives
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.generic import ListView, DetailView, CreateView, UpdateView, View
from django.urls import reverse_lazy
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from apps.accounts.mixins import TechnicienRequiredMixin, AdminRequiredMixin
from .models import Ticket, TicketHistory
from .forms import TicketCreateForm, TicketEditForm, TicketStatusForm, TicketAssignForm
from apps.ai_classifier.classifier import classifier
from apps.tickets.models import Category
from apps.comments.forms import CommentForm
def log_history(ticket, user, field, old_value, new_value):
    """Enregistre un changement dans l'historique du ticket."""
    TicketHistory.objects.create(
        ticket=ticket,
        changed_by=user,
        field_changed=field,
        old_value=str(old_value),
        new_value=str(new_value),
    )


def send_ticket_created_email(ticket, user):
    """Envoie un email de confirmation de création de ticket à l'utilisateur."""
    if not user.email:
        return

    subject = f"✓ Confirmation de création du ticket #{ticket.pk}"
    
    # Message HTML formaté
    html_message = f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; border: 1px solid #ddd; border-radius: 8px; padding: 20px;">
                <h2 style="color: #2c5aa0; border-bottom: 2px solid #2c5aa0; padding-bottom: 10px;">
                    Ticket #{ticket.pk} créé avec succès
                </h2>
                
                <p>Bonjour <strong>{user.get_full_name() or user.username}</strong>,</p>
                
                <p>Nous confirmons la réception de votre demande d'assistance. Voici les détails de votre ticket :</p>
                
                <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p><strong>Titre :</strong> {ticket.title}</p>
                    <p><strong>Catégorie :</strong> {ticket.category.name if ticket.category else 'Non assignée'}</p>
                    <p><strong>Priorité :</strong> {ticket.get_priority_display()}</p>
                    <p><strong>Numéro de ticket :</strong> #{ticket.pk}</p>
                    <p><strong>Date de création :</strong> {ticket.created_at.strftime('%d/%m/%Y à %H:%M')}</p>
                </div>
                
                <p>Votre demande a été enregistrée et sera prise en considération par notre équipe de support dans les plus brefs délais.</p>
                
                <p>Vous pouvez suivre l'évolution de votre ticket à tout moment en consultant votre compte sur notre plateforme.</p>
                
                <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                
                <p style="color: #666; font-size: 12px;">
                    <strong>Équipe Smart Claim</strong><br>
                    Support technique<br>
                    Merci de votre confiance !
                </p>
            </div>
        </body>
    </html>
    """
    
    # Message texte simple
    text_message = f"""
Bonjour {user.get_full_name() or user.username},

Nous confirmons la réception de votre demande d'assistance. Voici les détails de votre ticket :

Titre : {ticket.title}
Catégorie : {ticket.category.name if ticket.category else 'Non assignée'}
Priorité : {ticket.get_priority_display()}
Numéro de ticket : #{ticket.pk}
Date de création : {ticket.created_at.strftime('%d/%m/%Y à %H:%M')}

Votre demande a été enregistrée et sera prise en considération par notre équipe de support dans les plus brefs délais.

Vous pouvez suivre l'évolution de votre ticket à tout moment en consultant votre compte sur notre plateforme.

---
Équipe Smart Claim
Support technique
Merci de votre confiance !
    """
    
    try:
        # Utiliser EmailMultiAlternatives pour supporter HTML et texte
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@incidentops.local'),
            to=[user.email]
        )
        email.attach_alternative(html_message, "text/html")
        email.send(fail_silently=False)
    except Exception as e:
        # Log l'erreur sans bloquer le flux
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erreur lors de l'envoi du mail pour le ticket #{ticket.pk}: {str(e)}")


class TicketListView(LoginRequiredMixin, ListView):
    model = Ticket
    template_name = 'tickets/list.html'
    context_object_name = 'tickets'
    paginate_by = 15

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            qs = Ticket.objects.all()
        elif user.role == 'technicien':
            qs = Ticket.objects.filter(assigned_to=user)
        else:
            qs = Ticket.objects.filter(created_by=user)

        # Filtres optionnels via GET
        status = self.request.GET.get('status')
        priority = self.request.GET.get('priority')
        if status:
            qs = qs.filter(status=status)
        if priority:
            qs = qs.filter(priority=priority)

        return qs.select_related('category', 'created_by', 'assigned_to')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['status_choices'] = Ticket.Status.choices
        ctx['priority_choices'] = Ticket.Priority.choices
        ctx['current_status'] = self.request.GET.get('status', '')
        ctx['current_priority'] = self.request.GET.get('priority', '')
        return ctx


class TicketCreateView(LoginRequiredMixin, CreateView):
    model = Ticket
    form_class = TicketCreateForm
    template_name = 'tickets/create.html'

    def form_valid(self, form):
        ticket = form.save(commit=False)
        ticket.created_by = self.request.user
        ticket.status = Ticket.Status.OPEN

        # Appel du classifieur IA au moment de la sauvegarde
        categories = list(Category.objects.all())
        result = classifier.classify(ticket.title, ticket.description, categories)

        if result['category']:
            ticket.ai_suggested_category = result['category']
        if result['priority']:
            ticket.ai_suggested_priority = result['priority']

        ticket.save()
        log_history(ticket, self.request.user, 'status', '', Ticket.Status.OPEN)
        send_ticket_created_email(ticket, self.request.user)
        messages.success(self.request, f"Ticket #{ticket.pk} créé avec succès.")
        return redirect('tickets:detail', pk=ticket.pk)


class TicketDetailView(LoginRequiredMixin, DetailView):
    model = Ticket
    template_name = 'tickets/detail.html'
    context_object_name = 'ticket'

    def get_object(self):
        ticket = get_object_or_404(Ticket, pk=self.kwargs['pk'])
        user = self.request.user
        # Un utilisateur normal ne peut voir que ses propres tickets
        if user.role == 'user' and ticket.created_by != user:
            raise PermissionDenied
        return ticket

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ticket = self.get_object()
        user = self.request.user
        allowed = ticket.get_allowed_transitions(user.role)
        if allowed:
            ctx['status_form'] = TicketStatusForm(allowed_transitions=allowed)
        if user.role == 'admin':
            ctx['assign_form'] = TicketAssignForm(instance=ticket)
        ctx['history'] = ticket.history.select_related('changed_by')
        ctx['comments'] = ticket.comments.select_related('author')
        ctx['comment_form'] = CommentForm(user=user)
        return ctx


class TicketEditView(LoginRequiredMixin, UpdateView):
    model = Ticket
    form_class = TicketEditForm
    template_name = 'tickets/edit.html'

    def get_object(self):
        ticket = get_object_or_404(Ticket, pk=self.kwargs['pk'])
        # Seul le créateur peut modifier, et uniquement si le ticket est ouvert
        if ticket.created_by != self.request.user or not ticket.is_open:
            raise PermissionDenied
        return ticket

    def get_success_url(self):
        return reverse_lazy('tickets:detail', kwargs={'pk': self.object.pk})


class TicketStatusUpdateView(LoginRequiredMixin, View):

    def post(self, request, pk):
        ticket = get_object_or_404(Ticket, pk=pk)
        user = request.user
        allowed = ticket.get_allowed_transitions(user.role)
        form = TicketStatusForm(request.POST, allowed_transitions=allowed)

        if not form.is_valid():
            messages.error(request, "Formulaire invalide.")
            return redirect('tickets:detail', pk=pk)

        new_status = form.cleaned_data['new_status']

        if not ticket.can_transition_to(new_status, user.role):
            messages.error(request, "Transition de statut non autorisée.")
            return redirect('tickets:detail', pk=pk)

        old_status = ticket.status
        ticket.status = new_status

        if new_status == Ticket.Status.RESOLVED:
            ticket.resolved_at = timezone.now()

        ticket.save()
        log_history(ticket, user, 'status', old_status, new_status)
        messages.success(request, f"Statut mis à jour : {ticket.get_status_display()}")
        return redirect('tickets:detail', pk=pk)


class TicketAssignView(AdminRequiredMixin, View):

    def post(self, request, pk):
        ticket = get_object_or_404(Ticket, pk=pk)
        form = TicketAssignForm(request.POST, instance=ticket)

        if not form.is_valid():
            messages.error(request, "Affectation invalide.")
            return redirect('tickets:detail', pk=pk)

        old_assigned = ticket.assigned_to
        ticket = form.save(commit=False)
        ticket.status = Ticket.Status.ASSIGNED
        ticket.save()

        log_history(ticket, request.user, 'assigned_to',
                    old_assigned or '—',
                    ticket.assigned_to)
        messages.success(request, f"Ticket affecté à {ticket.assigned_to}.")
        return redirect('tickets:detail', pk=pk)
