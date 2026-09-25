"""Shared test configuration.

Unit tests need no services. Integration tests require DATABASE_URL to point
at a disposable PostgreSQL database with pgvector; they are skipped otherwise.
"""

from __future__ import annotations

import os
import tempfile

os.environ.setdefault("ENVIRONMENT", "test")
# The test client sends Host: testserver.
os.environ.setdefault("ALLOWED_HOSTS", '["localhost", "127.0.0.1", "testserver"]')
os.environ.setdefault("STORAGE_ROOT", tempfile.mkdtemp(prefix="product-b-storage-"))
