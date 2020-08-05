import datetime
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers import (
    SchedulerNotRunningError,
    SchedulerAlreadyRunningError,
)
from apscheduler.jobstores.base import ConflictingIdError

from multiprocessing.pool import ThreadPool

from flask import Flask, render_template, url_for, redirect, request, jsonify
from flask_sqlalchemy import SQLAlchemy  # type: ignore

from scrapper import run
from ui.graphs import create_plot

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


def sched_task(pool, save=False):
    results = run.multiple(pool, False)
    print("results", results)
    # TODO: Add results to database


#########################
# Views endpoints
#########################


@app.route("/")
def home():
    # TODO: add flash msg to base template
    return render_template("home.html")


@app.route("/users_list")
def users_list():
    return render_template("users_list.html")


@app.route("/add_user", methods=["GET", "POST"])
def add_user():
    if request.method == "POST":
        db_add_user(
            dni=request.form["username"],
            password=request.form["password"],
            name=request.form["name"],
        )
        # TODO: Add flask message
        return redirect(url_for("home"))
    return render_template("add_user.html")


#########################
# API Endpoints
#########################


@app.route("/get_all_users", methods=["GET"])
def get_all_users():
    return User.json()


@app.route("/get_plot/<dni>", methods=["GET"])
def get_plot(dni):
    user = User.get_by_dni(dni)
    plot = create_plot(dni, user.reads.all())
    return url_for("render_plot", _external=True)


@app.route("/historic_stats/<dni>", methods=["GET"])
def historic_stats(dni):
    user = User.get_by_dni(dni)
    stats = Read.historic_stats(id_=user.id)
    return stats


@app.route("/render_plot")
def render_plot():
    return render_template("_user_graph.html")


# Activate reading script
@app.route("/read")
def read():
    """Start the process of readings."""
    try:  # avoids start two jobs with same id
        pool = ThreadPool(4)
        print("Starting a new job")
        scheduler.add_job(
            **scheduler_config(sched_task, (pool,), datetime.datetime.now())
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


# db.create_all()
from ui.models import User, Read, db_add_user  # noqa

if __name__ == "__main__":
    app.run(debug=True)
