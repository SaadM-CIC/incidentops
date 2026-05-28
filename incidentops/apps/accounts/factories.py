import factory
from django.contrib.auth.hashers import make_password
from .models import CustomUser


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CustomUser

    username = factory.Sequence(lambda n: f'user_{n}')
    email = factory.LazyAttribute(lambda o: f'{o.username}@test.com')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    password = factory.LazyFunction(lambda: make_password('testpass123'))
    role = CustomUser.Role.USER
    is_active = True


class TechnicianFactory(UserFactory):
    username = factory.Sequence(lambda n: f'tech_{n}')
    role = CustomUser.Role.TECHNICIEN


class AdminFactory(UserFactory):
    username = factory.Sequence(lambda n: f'admin_{n}')
    role = CustomUser.Role.ADMIN