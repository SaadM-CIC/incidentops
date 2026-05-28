from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Avg, Q, F, ExpressionWrapper, DurationField
from django.db.models.functions import TruncMonth
from django.shortcuts import redirect
from django.utils import timezone
from django.views.generic import TemplateView
from datetime import timedelta

from apps.accounts.mixins import TechnicienRequiredMixin, AdminRequiredMixin
from apps.accounts.models import CustomUser
from apps.tickets.models import Ticket
from apps.notifications.models import Notification


class DashboardRedirectView(LoginRequiredMixin, TemplateView):
    """Redirige vers le bon dashboard selon le rôle."""

    def get(self, request, *args, **kwargs):
        role = request.user.role
        if role == 'admin':
            return redirect('dashboard:admin')
        elif role == 'technicien':
            return redirect('dashboard:technicien')
        return redirect('dashboard:user')


class UserDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/user.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        tickets = Ticket.objects.filter(created_by=user)

        ctx['total_tickets'] = tickets.count()
        ctx['open_tickets'] = tickets.filter(
            status__in=['open', 'pending_assignment', 'assigned', 'in_progress', 'waiting_info']
        ).count()
        ctx['resolved_tickets'] = tickets.filter(status='resolved').count()
        ctx['closed_tickets'] = tickets.filter(status='closed').count()

        ctx['recent_tickets'] = tickets.select_related(
            'category', 'assigned_to'
        ).order_by('-created_at')[:5]

        ctx['tickets_by_status'] = tickets.values(
            'status'
        ).annotate(count=Count('id')).order_by('status')

        ctx['tickets_by_priority'] = tickets.values(
            'priority'
        ).annotate(count=Count('id')).order_by('priority')

        ctx['unread_notifications'] = Notification.objects.filter(
            recipient=user, is_read=False
        ).order_by('-created_at')[:5]

        return ctx


class TechnicienDashboardView(TechnicienRequiredMixin, TemplateView):
    template_name = 'dashboard/technicien.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user

        assigned = Ticket.objects.filter(assigned_to=user)
        unassigned = Ticket.objects.filter(
            assigned_to=None,
            status='pending_assignment'
        )

        ctx['assigned_count'] = assigned.count()
        ctx['in_progress_count'] = assigned.filter(status='in_progress').count()
        ctx['resolved_today'] = assigned.filter(
            resolved_at__date=timezone.now().date()
        ).count()
        ctx['critical_count'] = assigned.filter(
            priority='critical',
            status__in=['assigned', 'in_progress']
        ).count()

        ctx['my_tickets'] = assigned.filter(
            status__in=['assigned', 'in_progress', 'waiting_info']
        ).select_related('category', 'created_by').order_by('-priority', '-created_at')[:10]

        ctx['unassigned_tickets'] = unassigned.select_related(
            'category', 'created_by'
        ).order_by('-priority', '-created_at')[:10]

        ctx['tickets_by_status'] = assigned.values(
            'status'
        ).annotate(count=Count('id'))

        # Temps moyen de résolution (en heures)
        resolved = assigned.filter(
            status__in=['resolved', 'closed'],
            resolved_at__isnull=False
        )
        avg_resolution = resolved.annotate(
            resolution_duration=ExpressionWrapper(
                F('resolved_at') - F('created_at'),
                output_field=DurationField(),
            )
        ).aggregate(avg=Avg('resolution_duration'))

        if avg_resolution['avg']:
            ctx['avg_resolution_hours'] = round(
                avg_resolution['avg'].total_seconds() / 3600,
                1,
            )
        else:
            ctx['avg_resolution_hours'] = None

        return ctx


class AdminDashboardView(AdminRequiredMixin, TemplateView):
    template_name = 'dashboard/admin.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        all_tickets = Ticket.objects.all()
        now = timezone.now()
        last_30_days = now - timedelta(days=30)

        # Compteurs globaux
        ctx['total_tickets'] = all_tickets.count()
        ctx['open_tickets'] = all_tickets.filter(
            status__in=['open', 'pending_assignment', 'assigned', 'in_progress', 'waiting_info']
        ).count()
        ctx['resolved_tickets'] = all_tickets.filter(status='resolved').count()
        ctx['critical_tickets'] = all_tickets.filter(
            priority='critical',
            status__in=['open', 'pending_assignment', 'assigned', 'in_progress']
        ).count()
        ctx['unassigned_tickets'] = all_tickets.filter(
            assigned_to=None,
            status__in=['open', 'pending_assignment']
        ).count()
        ctx['total_users'] = CustomUser.objects.filter(role='user').count()
        ctx['total_techniciens'] = CustomUser.objects.filter(role='technicien').count()

        # Répartitions
        ctx['tickets_by_status'] = all_tickets.values(
            'status'
        ).annotate(count=Count('id')).order_by('-count')

        ctx['tickets_by_priority'] = all_tickets.values(
            'priority'
        ).annotate(count=Count('id')).order_by('-count')

        ctx['tickets_by_category'] = all_tickets.values(
            'category__name'
        ).annotate(count=Count('id')).order_by('-count')[:8]

        # Charge des techniciens
        ctx['technicien_load'] = CustomUser.objects.filter(
            role__in=['technicien', 'admin']
        ).annotate(
            active_tickets=Count(
                'assigned_tickets',
                filter=Q(assigned_tickets__status__in=[
                    'assigned', 'in_progress', 'waiting_info'
                ])
            ),
            resolved_total=Count(
                'assigned_tickets',
                filter=Q(assigned_tickets__status__in=['resolved', 'closed'])
            )
        ).order_by('-active_tickets')

        # Tickets récents et critiques
        ctx['recent_tickets'] = all_tickets.select_related(
            'category', 'created_by', 'assigned_to'
        ).order_by('-created_at')[:8]

        ctx['critical_open'] = all_tickets.filter(
            priority='critical',
            status__in=['open', 'pending_assignment', 'assigned', 'in_progress']
        ).select_related('category', 'created_by', 'assigned_to').order_by('-created_at')

        # Évolution mensuelle sur 6 mois
        ctx['monthly_tickets'] = all_tickets.filter(
            created_at__gte=now - timedelta(days=180)
        ).annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(count=Count('id')).order_by('month')

        return ctx
