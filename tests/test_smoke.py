import pytest
from django.conf import settings
import os

@pytest.mark.django_db
def test_smoke_database_connection():
    from django.contrib.auth.models import User
    # Verify we can query the database
    assert User.objects.count() == 0
