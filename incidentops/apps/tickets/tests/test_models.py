import pytest
from django.utils import timezone
from apps.tickets.models import Ticket
from apps.tickets.factories import TicketFactory, CategoryFactory
from apps.accounts.factories import UserFactory, TechnicianFactory, AdminFactory


@pytest.mark.django_db
class TestTicketModel:

    def test_ticket_creation(self):
        ticket = TicketFactory()
        assert ticket.pk is not None
        assert ticket.status == Ticket.Status.OPEN
        assert ticket.priority == Ticket.Priority.MEDIUM
        assert ticket.is_open is True

    def test_ticket_str(self):
        ticket = TicketFactory(title="Problème réseau")
        assert str(ticket.pk) in str(ticket)
        assert "Problème réseau" in str(ticket)

    def test_is_open_false_when_resolved(self):
        ticket = TicketFactory(status=Ticket.Status.RESOLVED)
        assert ticket.is_open is False

    def test_is_open_false_when_closed(self):
        ticket = TicketFactory(status=Ticket.Status.CLOSED)
        assert ticket.is_open is False

    def test_priority_color(self):
        assert TicketFactory(priority='critical').priority_color == 'danger'
        assert TicketFactory(priority='high').priority_color == 'warning'
        assert TicketFactory(priority='medium').priority_color == 'info'
        assert TicketFactory(priority='low').priority_color == 'success'

    def test_allowed_transitions_user(self):
        ticket = TicketFactory(status=Ticket.Status.RESOLVED)
        transitions = ticket.get_allowed_transitions('user')
        assert Ticket.Status.CLOSED in transitions

    def test_allowed_transitions_technician(self):
        ticket = TicketFactory(status=Ticket.Status.ASSIGNED)
        transitions = ticket.get_allowed_transitions('technicien')
        assert Ticket.Status.IN_PROGRESS in transitions

    def test_no_transitions_for_closed_ticket(self):
        ticket = TicketFactory(status=Ticket.Status.CLOSED)
        transitions = ticket.get_allowed_transitions('admin')
        assert transitions == []

    def test_can_transition_to(self):
        ticket = TicketFactory(status=Ticket.Status.IN_PROGRESS)
        assert ticket.can_transition_to(Ticket.Status.RESOLVED, 'technicien') is True
        assert ticket.can_transition_to(Ticket.Status.CLOSED, 'technicien') is False


@pytest.mark.django_db
class TestCategoryModel:

    def test_keywords_list(self):
        category = CategoryFactory(keywords='réseau, wifi, internet')
        keywords = category.get_keywords_list()
        assert 'réseau' in keywords
        assert 'wifi' in keywords
        assert 'internet' in keywords

    def test_keywords_list_empty(self):
        category = CategoryFactory(keywords='')
        assert category.get_keywords_list() == []