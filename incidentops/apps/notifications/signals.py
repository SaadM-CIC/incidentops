from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.tickets.models import Ticket, TicketHistory
from apps.comments.models import Comment
from .models import Notification


def create_notification(recipient, ticket, notif_type, message):
    """Helper pour éviter la répétition."""
    if recipient:
        Notification.objects.create(
            recipient=recipient,
            ticket=ticket,
            notif_type=notif_type,
            message=message,
        )


@receiver(post_save, sender=TicketHistory)
def notify_on_status_change(sender, instance, created, **kwargs):
    if not created or instance.field_changed != 'status':
        return

    ticket = instance.ticket
    new_status = instance.new_value

    # Notifie le créateur du ticket si ce n'est pas lui qui a fait le changement
    if ticket.created_by != instance.changed_by:
        create_notification(
            recipient=ticket.created_by,
            ticket=ticket,
            notif_type=Notification.NotifType.STATUS_CHANGED,
            message=f"Votre ticket #{ticket.pk} est maintenant : {ticket.get_status_display()}"
        )

    # Notifie le technicien affecté si le ticket lui est assigné
    if new_status == 'assigned' and ticket.assigned_to:
        create_notification(
            recipient=ticket.assigned_to,
            ticket=ticket,
            notif_type=Notification.NotifType.TICKET_ASSIGNED,
            message=f"Le ticket #{ticket.pk} vous a été affecté : {ticket.title}"
        )

    # Notifie le créateur quand le ticket est résolu
    if new_status == 'resolved':
        create_notification(
            recipient=ticket.created_by,
            ticket=ticket,
            notif_type=Notification.NotifType.TICKET_RESOLVED,
            message=f"Votre ticket #{ticket.pk} a été résolu."
        )


@receiver(post_save, sender=Comment)
def notify_on_comment(sender, instance, created, **kwargs):
    if not created:
        return

    ticket = instance.ticket
    comment_author = instance.author

    # Ne pas notifier pour les notes internes
    if instance.is_internal:
        return

    # Notifie le créateur du ticket si ce n'est pas lui qui commente
    if ticket.created_by != comment_author:
        create_notification(
            recipient=ticket.created_by,
            ticket=ticket,
            notif_type=Notification.NotifType.NEW_COMMENT,
            message=f"Nouveau commentaire sur votre ticket #{ticket.pk}."
        )

    # Notifie le technicien si ce n'est pas lui qui commente
    if ticket.assigned_to and ticket.assigned_to != comment_author:
        create_notification(
            recipient=ticket.assigned_to,
            ticket=ticket,
            notif_type=Notification.NotifType.NEW_COMMENT,
            message=f"Nouveau commentaire sur le ticket #{ticket.pk} qui vous est affecté."
        )