import datetime
import logging
import sys
import traceback
from multiprocessing.pool import ThreadPool
from threading import Thread

from apscheduler.schedulers.blocking import BlockingScheduler

from scrapper import contador

error_log = logging.getLogger(__name__)
error_log.setLevel(logging.ERROR)
handler = logging.FileHandler(filename="logs/error.log", mode="a")
logger_formatter = logging.Formatter("[%(levelname)s] - %(message)s")
handler.setFormatter(logger_formatter)
error_log.addHandler(handler)

def run_safe(fn):
    """Deal with unexpected errors or miss behaves.

    There are still some edge cases where may occur some error and to avoid complete
    crashes, we log them here to fix later.
    TODO: Add error logs
    """

    READS = 0

    def _inner(*args):
        nonlocal READS
        errors = open("logs/error.log", "a")
        READS += 1
        try:
            contador.info_log.info(f"Lectura {READS}, {datetime.datetime.now()}")
            return fn(*args)  # TODO: Confirm
        except Exception as e:
            tb = traceback.format_exception(*sys.exc_info())
            error_log.error(tb)
            contador.info_log.error(e.args)
        errors.close()

    return _inner


@run_safe
def single():
    """Run script in a single thread."""
    return contador.read()


@run_safe
def multiple(pool, users, save: bool):
    """Run script inside a thread pool."""
    return contador.read_multiple(pool, users, save)
