import os
from logging.config import dictConfig

from celery import Celery
from celery.signals import setup_logging
import django
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "control_center.settings.dev")
django.setup()

app = Celery("chiliseed")
# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")


@setup_logging.connect
def config_loggers(*args, **kwags):  # noqa
    dictConfig(settings.LOGGING)


app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

app.conf.beat_schedule = {}
