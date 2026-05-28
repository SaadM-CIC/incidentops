# Create your models here.
from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    
    class Role(models.TextChoices):
        USER = 'user', 'Utilisateur'
        TECHNICIEN = 'technicien', 'Technicien'
        ADMIN = 'admin', 'Administrateur'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.USER,
        verbose_name="Rôle"
    )
    department = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Département / Service"
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Téléphone"
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        null=True,
        blank=True,
        verbose_name="Avatar"
    )
    bio = models.TextField(
        blank=True,
        verbose_name="Bio"
    )

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"

    def __str__(self):
        return f"{self.get_full_name()} ({self.username})"

    @property
    def is_technicien(self):
        return self.role == self.Role.TECHNICIEN

    @property
    def is_admin_user(self):
        return self.role == self.Role.ADMIN

    @property
    def is_regular_user(self):
        return self.role == self.Role.USER
