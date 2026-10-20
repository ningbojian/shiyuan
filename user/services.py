from __future__ import annotations

from django.db.models import F
from django.utils import timezone

from user.models import ReadingHistory

HISTORY_LIMIT = 50


def record_history(user, surname, limit: int = HISTORY_LIMIT) -> ReadingHistory:
    """Record one detail-page visit and keep only the newest ``limit`` rows."""
    entry, created = ReadingHistory.objects.get_or_create(
        user=user,
        surname=surname,
        defaults={"view_count": 1},
    )
    if not created:
        ReadingHistory.objects.filter(pk=entry.pk).update(
            view_count=F("view_count") + 1,
            last_viewed_at=timezone.now(),
        )

    stale_ids = list(
        ReadingHistory.objects.filter(user=user)
        .order_by("-last_viewed_at")
        .values_list("pk", flat=True)[limit:]
    )
    if stale_ids:
        ReadingHistory.objects.filter(pk__in=stale_ids).delete()
    return entry
