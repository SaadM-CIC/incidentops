from django.db import models
from django.conf import settings
from apps.tickets.models import Ticket


class Comment(models.Model):
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name="Ticket"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='comments',
        verbose_name="Auteur"
    )
    content = models.TextField(verbose_name="Contenu")
    is_internal = models.BooleanField(
        default=False,
        verbose_name="Note interne",
        help_text="Si coché, visible uniquement par les techniciens et admins"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Commentaire"
        verbose_name_plural = "Commentaires"
        ordering = ['created_at']

    def __str__(self):
        return f"Commentaire de {self.author} sur #{self.ticket.pk}"