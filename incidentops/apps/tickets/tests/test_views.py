import pytest
from django.urls import reverse
from apps.tickets.models import Ticket
from apps.tickets.factories import TicketFactory, CategoryFactory
from apps.accounts.factories import UserFactory, TechnicianFactory, AdminFactory


@pytest.mark.django_db
class TestTicketListView:

    def test_redirect_if_not_logged_in(self, client):
        response = client.get(reverse('tickets:list'))
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_user_sees_only_own_tickets(self, client):
        user = UserFactory()
        other_user = UserFactory()
        my_ticket = TicketFactory(created_by=user)
        other_ticket = TicketFactory(created_by=other_user)

        client.force_login(user)
        response = client.get(reverse('tickets:list'))

        assert response.status_code == 200
        tickets = response.context['tickets']
        assert my_ticket in tickets
        assert other_ticket not in tickets

    def test_admin_sees_all_tickets(self, client):
        admin = AdminFactory()
        user1 = UserFactory()
        user2 = UserFactory()
        ticket1 = TicketFactory(created_by=user1)
        ticket2 = TicketFactory(created_by=user2)

        client.force_login(admin)
        response = client.get(reverse('tickets:list'))

        assert response.status_code == 200
        tickets = response.context['tickets']
        assert ticket1 in tickets
        assert ticket2 in tickets


@pytest.mark.django_db
class TestTicketCreateView:

    def test_create_ticket_sets_creator(self, client):
        user = UserFactory()
        category = CategoryFactory()
        client.force_login(user)

        response = client.post(reverse('tickets:create'), {
            'title': 'Mon problème réseau',
            'description': 'Je ne peux plus me connecter au wifi',
            'category': category.pk,
            'priority': 'medium',
        })

        assert Ticket.objects.filter(created_by=user).exists()
        ticket = Ticket.objects.get(created_by=user)
        assert ticket.status == Ticket.Status.OPEN

    def test_create_ticket_requires_login(self, client):
        response = client.post(reverse('tickets:create'), {})
        assert response.status_code == 302


@pytest.mark.django_db
class TestTicketDetailView:

    def test_user_cannot_see_other_user_ticket(self, client):
        user = UserFactory()
        other_user = UserFactory()
        ticket = TicketFactory(created_by=other_user)

        client.force_login(user)
        response = client.get(reverse('tickets:detail', kwargs={'pk': ticket.pk}))
        assert response.status_code == 403

    def test_admin_can_see_any_ticket(self, client):
        admin = AdminFactory()
        user = UserFactory()
        ticket = TicketFactory(created_by=user)

        client.force_login(admin)
        response = client.get(reverse('tickets:detail', kwargs={'pk': ticket.pk}))
        assert response.status_code == 200


@pytest.mark.django_db
class TestTicketStatusUpdate:

    def test_technician_can_update_status(self, client):
        tech = TechnicianFactory()
        ticket = TicketFactory(
            status=Ticket.Status.ASSIGNED,
            assigned_to=tech
        )

        client.force_login(tech)
        response = client.post(
            reverse('tickets:status_update', kwargs={'pk': ticket.pk}),
            {'new_status': Ticket.Status.IN_PROGRESS, 'comment': ''}
        )

        ticket.refresh_from_db()
        assert ticket.status == Ticket.Status.IN_PROGRESS

    def test_invalid_transition_rejected(self, client):
        user = UserFactory()
        ticket = TicketFactory(
            status=Ticket.Status.OPEN,
            created_by=user
        )

        client.force_login(user)
        client.post(
            reverse('tickets:status_update', kwargs={'pk': ticket.pk}),
            {'new_status': Ticket.Status.RESOLVED, 'comment': ''}
        )

        ticket.refresh_from_db()
        # Le statut ne doit pas avoir changé
        assert ticket.status == Ticket.Status.OPEN