from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CustomUser, Manager, Staff

@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        if instance.role == 'manager' and not hasattr(instance, 'manager'):
            Manager.objects.create(user=instance)
        elif instance.role == 'staff' and not hasattr(instance, 'staff'):
            Staff.objects.create(user=instance)

