"""Run script during intervals."""

import datetime
import logging
import sys
import traceback
from multiprocessing.pool import ThreadPool
import multiprocessing
from threading import Thread

from apscheduler.schedulers.blocking import BlockingScheduler

from scrapper import run, contador


def scheduler_config(fn, args, start):
    return {
        "func": fn,
        "args": args,
        "trigger": "interval",
        "minutes": run.FREQUENCY,
        "next_run_time": start,
    }


if __name__ == "__main__":
    scheduler = BlockingScheduler()
    try:
        mode = sys.argv[1]
        if mode == "multiple":
            workers = multiprocessing.cpu_count()
            pool = ThreadPool(workers)
            scheduler.add_job(
                **scheduler_config(run.multiple, (pool,), datetime.datetime.now())
            )

            scheduler.start()
        else:
            contador.info_log.error(f"mode value error: can't be <{mode}>")
    except IndexError:
        # no value passed, run single thread script
        scheduler.add_job(**scheduler_config(run.single, None, datetime.datetime.now()))
        scheduler.start()
