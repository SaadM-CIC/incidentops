from django.db import models
from django.conf import settings
from apps.tickets.models import Ticket


class Notification(models.Model):

    class NotifType(models.TextChoices):
        STATUS_CHANGED = 'status_changed', 'Statut modifié'
        TICKET_ASSIGNED = 'ticket_assigned', 'Ticket affecté'
        NEW_COMMENT = 'new_comment', 'Nouveau commentaire'
        TICKET_RESOLVED = 'ticket_resolved', 'Ticket résolu'

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name="Destinataire"
    )
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name="Ticket"
    )
    notif_type = models.CharField(
        max_length=30,
        choices=NotifType.choices,
        verbose_name="Type"
    )
    message = models.CharField(max_length=255, verbose_name="Message")
    is_read = models.BooleanField(default=False, verbose_name="Lu")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.notif_type}] → {self.recipient} | {self.message}"