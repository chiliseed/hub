"""Main configuration module for Chiliseed API."""

# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
from .scheduler import app as scheduler

__all__ = ("scheduler",)
