"""Celery application entrypoint: `celery -A research_worker.app worker`."""

from __future__ import annotations

from research_api.config import get_settings
from research_api.platform.logging import configure_logging
from research_api.platform.queue import get_celery

configure_logging(get_settings().log_level)

celery_app = get_celery()
celery_app.autodiscover_tasks(["research_worker"], related_name="tasks", force=True)
