# accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = (
        ("customer", "Customer"),
        ("restaurant", "Restaurant"),
        ("admin", "Admin"),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="customer")
    profile_image_url = models.URLField(blank=True, null=True)


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class BlacklistedRefreshToken(models.Model):
    """
    Store JTI of refresh tokens that are no longer valid (logout/rotation).
    """

    jti = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.jti
