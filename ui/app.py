import datetime
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers import (
    SchedulerNotRunningError,
    SchedulerAlreadyRunningError,
)
from apscheduler.jobstores.base import ConflictingIdError

from multiprocessing.pool import ThreadPool

from flask import Flask, render_template, url_for, redirect, request
from flask_sqlalchemy import SQLAlchemy  # type: ignore

from scrapper import run

# from ui.models import crud

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
log = logging.getLogger("werkzeug")
log.disabled = True

scheduler = BackgroundScheduler()


def scheduler_config(fn, args, start):
    return {
        "func": fn,
        "args": args,
        "trigger": "interval",
        "minutes": 15,
        "next_run_time": start,
        "id": "contador",
    }


@app.before_first_request
def start_scheduler():
    print("Starting scheduler")
    scheduler.start()


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/add_user", methods=["GET", "POST"])
def add_user():
    if request.method == "POST":
        add_user(
            request.form["username"], request.form["password"], request.form["name"]
        )
        # TODO: Add flask message
        return redirect(url_for("home"))
    return render_template("add_user.html")


@app.route("/read")
def read():
    """Start the process of readings."""
    try:  # avoids start two jobs with same id
        pool = ThreadPool(4)
        print("Starting a new job")
        scheduler.add_job(
            **scheduler_config(run.multiple, (pool,), datetime.datetime.now())
        )
    except ConflictingIdError:
        pass

    return redirect(url_for("home"))


@app.route("/stop_read")
def stop_read():
    """Stop the process of readings."""
    print("Stopping job")
    scheduler.remove_job("contador")
    return redirect(url_for("home"))


# from ui.models import User, Read, add_user  # noqa
db.create_all()
if __name__ == "__main__":
    app.run(debug=True)
