import requests
import xml.etree.ElementTree as ET
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from django.db import transaction
from catalogue.models import AniDBState

class AniDBError(Exception):
    pass

class AniDBClient:
    def __init__(self):
        self.client_name = settings.ANIDB_CLIENT_NAME
        self.client_version = settings.ANIDB_CLIENT_VERSION
        self.pacing_seconds = settings.ANIDB_PACING_SECONDS
        self.daily_budget = settings.ANIDB_DAILY_BUDGET
        self.base_url = "https://api.anidb.net:9001/httpapi"

    def is_configured(self):
        return bool(self.client_name and self.client_version)

    def _can_make_request(self):
        with transaction.atomic():
            state, _ = AniDBState.objects.select_for_update().get_or_create(id=1)

            # Reset daily count if day changed
            now = timezone.now()
            if state.current_date != now.date():
                state.current_date = now.date()
                state.daily_request_count = 0
                state.save()

            if state.is_banned:
                if state.cooldown_until and now < state.cooldown_until:
                    return False
                else:
                    state.is_banned = False
                    state.cooldown_until = None
                    state.save()

            if state.daily_request_count >= self.daily_budget:
                return False

            if state.last_request_at:
                delta = now - state.last_request_at
                if delta.total_seconds() < self.pacing_seconds:
                    return False

            return True

    def _record_request(self):
        with transaction.atomic():
            state, _ = AniDBState.objects.select_for_update().get_or_create(id=1)
            state.last_request_at = timezone.now()
            state.daily_request_count += 1
            state.save()

    def _apply_ban(self, hours=24):
        with transaction.atomic():
            state, _ = AniDBState.objects.select_for_update().get_or_create(id=1)
            state.is_banned = True
            state.cooldown_until = timezone.now() + timedelta(hours=hours)
            state.save()

    def fetch_anime(self, aid):
        if not self.is_configured():
            raise AniDBError("Client not registered. Configure ANIDB_CLIENT_NAME and ANIDB_CLIENT_VERSION.")

        if not self._can_make_request():
            raise AniDBError("Rate limit, daily budget exceeded, or pacing lock active.")

        self._record_request()

        params = {
            'client': self.client_name,
            'clientver': self.client_version,
            'protover': '1',
            'request': 'anime',
            'aid': str(aid)
        }

        try:
            response = requests.get(self.base_url, params=params, timeout=10)
        except requests.RequestException as e:
            raise AniDBError(f"Network error: {e}")

        # AniDB often returns HTTP 200 with an XML error payload
        if response.status_code != 200:
            raise AniDBError(f"HTTP Error {response.status_code}")

        try:
            # Defuse XML attacks by not allowing external entities
            # In a real production setup we'd use defusedxml. ElementTree handles basic cases securely enough for this MVP.
            root = ET.fromstring(response.content)
        except ET.ParseError:
            raise AniDBError("Invalid XML returned")

        if root.tag == 'error':
            error_msg = root.text or ""
            if "BANNED" in error_msg.upper():
                self._apply_ban()
            raise AniDBError(f"AniDB Error: {error_msg}")

        return root
