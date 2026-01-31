from django.utils import timezone

from account.models import ShopIntegration
from foodCreate.models import Products
from foodCreate.integrations.pos import build_connector


def sync_pos_integrations():
    """Sync inventory data from POS/ERP providers."""
    integrations = ShopIntegration.objects.select_related("shop").all()
    results = []

    for integration in integrations:
        connector = build_connector(integration)
        if not connector:
            integration.sync_status = "unsupported"
            integration.save(update_fields=["sync_status"])
            continue

        if not integration.access_token:
            integration.sync_status = "missing_token"
            integration.save(update_fields=["sync_status"])
            continue

        inventory_items = connector.fetch_inventory()
        for item in inventory_items:
            if not item.barcode:
                continue
            product = Products.objects.filter(shop=integration.shop, barcode=item.barcode).first()
            if product:
                product.stock = item.stock
                product.save(update_fields=["stock"])
        integration.last_synced_at = timezone.now()
        integration.sync_status = "synced"
        integration.save(update_fields=["last_synced_at", "sync_status"])
        results.append((integration, inventory_items))

    return results
