"""Adds counts / links for global admin banners (see templates/admin/base_site.html)."""

from django.db import DatabaseError


def admin_global_alerts(request):
    path = getattr(request, 'path', '') or ''
    if not path.startswith('/admin/'):
        return {}

    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated or not user.is_staff:
        return {}

    pending_orders = 0
    try:
        from commerce.models import Order

        pending_orders = Order.objects.filter(is_seen_moderator=True).count()
    except (ImportError, LookupError, DatabaseError):
        pass

    return {
        'admin_pending_orders_count': pending_orders,
    }
