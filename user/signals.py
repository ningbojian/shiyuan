from __future__ import annotations

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from user.models import Profile


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def ensure_profile(sender, instance, created: bool, **kwargs) -> None:
    if created:
        Profile.objects.get_or_create(user=instance)
