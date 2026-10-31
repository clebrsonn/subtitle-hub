import xml.etree.ElementTree as ET
from datetime import timedelta
import time
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from django.db.models import Q
from catalogue.models import Work, ExternalMapping
from catalogue.anidb import AniDBClient, AniDBError
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Enrich pending works by fetching data from AniDB (with 24h caching).'

    def handle(self, *args, **options):
        client = AniDBClient()
        if not client.is_configured():
            self.stdout.write(self.style.WARNING("AniDB client not configured. Skipping enrichment."))
            return

        cutoff_time = timezone.now() - timedelta(hours=24)
        mappings_to_update = ExternalMapping.objects.filter(Q(provider='anidb'))

        final_mappings = []
        for m in mappings_to_update:
            if m.retrieval_time is None or m.retrieval_time < cutoff_time:
                final_mappings.append(m)

        for mapping in final_mappings:
            aid = mapping.external_id

            # Wait if pacing lock is active
            while not client._can_make_request():
                self.stdout.write(self.style.WARNING(f"Pacing or budget limits active. Waiting..."))
                # Basic sleep to respect pacing
                time.sleep(settings.ANIDB_PACING_SECONDS + 1)

            try:
                self.stdout.write(f"Fetching metadata for AniDB aid {aid}...")
                root = client.fetch_anime(aid)

                titles = root.findall('.//title')
                main_title = None
                for t in titles:
                    if t.text:
                       main_title = t.text
                for t in titles:
                    if t.get('type') == 'main':
                        main_title = t.text
                        break

                with transaction.atomic():
                    mapping.retrieval_time = timezone.now()

                    if main_title and mapping.work:
                        mapping.work.title = main_title
                        mapping.work.save()

                    mapping.save()

                self.stdout.write(self.style.SUCCESS(f"Successfully enriched AniDB aid {aid}."))

            except AniDBError as e:
                self.stdout.write(self.style.ERROR(f"Failed to fetch aid {aid}: {e}"))
                if "BANNED" in str(e):
                    self.stdout.write(self.style.ERROR("Halting enrichment due to AniDB ban."))
                    break

        self.stdout.write(self.style.SUCCESS("Enrichment run complete."))
