import logging
import sys

FORMAT = (
    "%(asctime)-27s %(name)-22s %(funcName)s %(filename)s %(levelname)s %(message)s"
)
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format=FORMAT)


def get_logger(name: str) -> logging.Logger:
    """Returns configured logger."""
    return logging.getLogger(f"{name}-infra-executor")
