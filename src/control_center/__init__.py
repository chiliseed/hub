"""Main configuration module for Chiliseed API."""
import signal
import sys


def handle_shutdown(signum, frame):
    from .scheduler import scheduler
    print('Signal handler called with signal ', signum)
    print("waiting for scheduler jobs to finish...")
    scheduler.shutdown()
    print('stopped'.upper())
    sys.exit(0)


print("Registering to kill events")
signal.signal(signal.SIGINT, handle_shutdown)
signal.signal(signal.SIGTERM, handle_shutdown)
