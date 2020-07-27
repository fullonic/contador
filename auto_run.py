"""Run script during intervals."""

import logging
import sys
import time
import traceback
from multiprocessing.pool import ThreadPool

import contador

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

    def _inner(*args):
        reads = 1
        errors = open("logs/error.log", "a")
        while True:
            try:
                fn(*args)
                reads += 1
                time.sleep(10 * 60)  # TODO: import from cfg file
            except Exception as e:
                tb = traceback.format_exception(*sys.exc_info())
                error_log.error(tb)
                contador.info_log.error(e.args)
        errors.close()

    return _inner


@run_safe
def run():
    """Run script in a single thread."""
    return contador.read()


@run_safe
def run_multiple(pool):
    """Run script inside a thread pool."""
    return contador.read_multiple(pool)


if __name__ == "__main__":
    try:
        mode = sys.argv[1]
        if mode == "multiple":
            pool = ThreadPool(4)
            run_multiple(pool)
        else:
            print(f"mode value error: can't be <{mode}>")
    except IndexError:
        # no value passed, run single thread script
        run()
