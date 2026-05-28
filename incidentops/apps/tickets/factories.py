import factory
from .models import Ticket, Category
from apps.accounts.factories import UserFactory


class CategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Category

    name = factory.Sequence(lambda n: f'Catégorie {n}')
    description = factory.Faker('sentence')
    keywords = factory.LazyAttribute(lambda o: f'{o.name.lower()}, test, exemple')


class TicketFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Ticket

    title = factory.Faker('sentence', nb_words=6)
    description = factory.Faker('paragraph')
    category = factory.SubFactory(CategoryFactory)
    priority = Ticket.Priority.MEDIUM
    status = Ticket.Status.OPEN
    created_by = factory.SubFactory(UserFactory)