import os
import atexit

from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore, register_events

scheduler = BackgroundScheduler()

if not "PYTEST_CURRENT_TEST" in os.environ:
    atexit.register(lambda: scheduler.shutdown(wait=False))

    scheduler.add_jobstore(DjangoJobStore(), "default")
    register_events(scheduler)

    scheduler.start()
    print("Scheduler started")
