from django.core.management.base import BaseCommand

from foodCreate.tasks import sync_pos_integrations


class Command(BaseCommand):
    help = "Sync inventory data from POS/ERP integrations."

    def handle(self, *args, **options):
        results = sync_pos_integrations()
        self.stdout.write(self.style.SUCCESS(f"Synced {len(results)} integration(s)."))
