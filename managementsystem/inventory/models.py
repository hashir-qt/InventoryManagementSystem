from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('manager', 'Manager'),
        ('staff', 'Staff'),
        ('admin', 'Admin'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='staff')

    def __str__(self):
        return f"{self.username} ({self.role})"

# Store Model
class Store(models.Model):
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255, default='No Address Provided')
    phone_number = models.CharField(max_length=20, default='No Number Provided')
    email = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now)

    manager = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_stores',
    )
    staff = models.ManyToManyField(
        CustomUser,
        blank=True,
        related_name='staffed_stores',
    )

    def __str__(self):
        return self.name

# Category Model
class Category(models.Model):
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name

# Product Model
class Product(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField()
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)

    created_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products_created'
    )
    updated_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products_updated'
    )

    def __str__(self):
        return self.name

# Manager Model

class Manager(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    store = models.OneToOneField(Store, on_delete=models.CASCADE, related_name='store_manager', null=True, blank=True)
    
    def __str__(self):
        store_name = self.store.name if self.store else "No Store Assigned"
        return f"{self.user.username} - {store_name}"

# Staff Model
class Staff(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    store = models.ForeignKey(Store, related_name='store_staff', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        store_name = self.store.name if self.store else "No Store Assigned"
        return f"{self.user.username} - {store_name}"
