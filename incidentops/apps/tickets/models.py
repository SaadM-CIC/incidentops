from django.db import models
from django.conf import settings
from .validators import validate_file_extension, validate_file_size



class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Nom")
    description = models.TextField(blank=True, verbose_name="Description")
    keywords = models.TextField(
        blank=True,
        verbose_name="Mots-clés IA",
        help_text="Mots-clés séparés par des virgules, utilisés par le module IA"
    )

    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_keywords_list(self):
        return [k.strip().lower() for k in self.keywords.split(',') if k.strip()]


class Ticket(models.Model):

    class Priority(models.TextChoices):
        LOW = 'low', 'Faible'
        MEDIUM = 'medium', 'Moyenne'
        HIGH = 'high', 'Élevée'
        CRITICAL = 'critical', 'Critique'

    class Status(models.TextChoices):
        OPEN = 'open', 'Ouvert'
        PENDING_ASSIGNMENT = 'pending_assignment', 'En attente d\'affectation'
        ASSIGNED = 'assigned', 'Affecté'
        IN_PROGRESS = 'in_progress', 'En cours de traitement'
        WAITING_INFO = 'waiting_info', 'En attente d\'information'
        RESOLVED = 'resolved', 'Résolu'
        CLOSED = 'closed', 'Fermé'
        CANCELLED = 'cancelled', 'Annulé'

    # Transitions autorisées par rôle
    # clé = statut actuel, valeur = statuts accessibles
    ALLOWED_TRANSITIONS = {
        'user': {
            Status.OPEN: [],
            Status.WAITING_INFO: [Status.IN_PROGRESS],
            Status.RESOLVED: [Status.CLOSED],
        },
        'technicien': {
            Status.PENDING_ASSIGNMENT: [Status.ASSIGNED],
            Status.ASSIGNED: [Status.IN_PROGRESS],
            Status.IN_PROGRESS: [Status.WAITING_INFO, Status.RESOLVED],
            Status.WAITING_INFO: [Status.IN_PROGRESS, Status.RESOLVED],
        },
        'admin': {
            Status.OPEN: [Status.PENDING_ASSIGNMENT, Status.CANCELLED],
            Status.PENDING_ASSIGNMENT: [Status.ASSIGNED, Status.CANCELLED],
            Status.ASSIGNED: [Status.IN_PROGRESS, Status.CANCELLED],
            Status.IN_PROGRESS: [Status.WAITING_INFO, Status.RESOLVED, Status.CANCELLED],
            Status.WAITING_INFO: [Status.IN_PROGRESS, Status.RESOLVED, Status.CANCELLED],
            Status.RESOLVED: [Status.CLOSED, Status.IN_PROGRESS],
        },
    }

    title = models.CharField(max_length=200, verbose_name="Titre")
    description = models.TextField(verbose_name="Description")
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='tickets',
        verbose_name="Catégorie"
    )
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM,
        verbose_name="Priorité"
    )
    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.OPEN,
        verbose_name="Statut"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='submitted_tickets',
        verbose_name="Créé par"
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='assigned_tickets',
        verbose_name="Technicien affecté"
    )
    attachment = models.FileField(
        upload_to='tickets/attachments/',
     null=True, blank=True,
        validators=[validate_file_extension, validate_file_size],
        verbose_name="Pièce jointe"
    )

    # Suggestions du module IA (remplies automatiquement)
    ai_suggested_category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='ai_suggested_tickets',
        verbose_name="Catégorie suggérée par l'IA"
    )
    ai_suggested_priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        blank=True,
        verbose_name="Priorité suggérée par l'IA"
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")
    resolved_at = models.DateTimeField(null=True, blank=True, verbose_name="Résolu le")

    class Meta:
        verbose_name = "Ticket"
        verbose_name_plural = "Tickets"
        ordering = ['-created_at']

    def __str__(self):
        return f"#{self.pk} — {self.title}"

    def get_allowed_transitions(self, user_role):
        """Retourne les statuts vers lesquels ce ticket peut transitionner."""
        transitions = self.ALLOWED_TRANSITIONS.get(user_role, {})
        return transitions.get(self.status, [])

    def can_transition_to(self, new_status, user_role):
        return new_status in self.get_allowed_transitions(user_role)

    @property
    def is_open(self):
        return self.status not in [
            self.Status.RESOLVED,
            self.Status.CLOSED,
            self.Status.CANCELLED
        ]

    @property
    def priority_color(self):
        return {
            'low': 'success',
            'medium': 'info',
            'high': 'warning',
            'critical': 'danger',
        }.get(self.priority, 'secondary')

    @property
    def status_color(self):
        return {
            'open': 'primary',
            'pending_assignment': 'secondary',
            'assigned': 'info',
            'in_progress': 'warning',
            'waiting_info': 'warning',
            'resolved': 'success',
            'closed': 'dark',
            'cancelled': 'danger',
        }.get(self.status, 'secondary')


class TicketHistory(models.Model):
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name='history',
        verbose_name="Ticket"
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Modifié par"
    )
    field_changed = models.CharField(max_length=50, verbose_name="Champ modifié")
    old_value = models.CharField(max_length=200, blank=True, verbose_name="Ancienne valeur")
    new_value = models.CharField(max_length=200, blank=True, verbose_name="Nouvelle valeur")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Date")

    class Meta:
        verbose_name = "Historique"
        verbose_name_plural = "Historiques"
        ordering = ['-timestamp']

    def __str__(self):
        return f"#{self.ticket.pk} — {self.field_changed} ({self.timestamp:%d/%m/%Y %H:%M})"
