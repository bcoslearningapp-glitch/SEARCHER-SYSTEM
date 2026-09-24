"""Shared test configuration.

Unit tests need no services. Integration tests require DATABASE_URL to point
at a disposable PostgreSQL database with pgvector; they are skipped otherwise.
"""

from __future__ import annotations

import os

os.environ.setdefault("ENVIRONMENT", "test")
