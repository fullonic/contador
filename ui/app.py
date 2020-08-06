import datetime
import json
import logging
import sqlite3
from multiprocessing.pool import ThreadPool
from pathlib import Path
from typing import List

from apscheduler.jobstores.base import ConflictingIdError
from apscheduler.schedulers import (
    SchedulerAlreadyRunningError,
    SchedulerNotRunningError,
)
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, flash, jsonify, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy  # type: ignore

from scrapper import run
from scrapper.contador import get_config
from ui.graphs import create_barchart

# db.create_all()


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///read_db.db"
app.config["SECRET_KEY"] = "only_for_local_networks"
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


def sched_task(pool: ThreadPool, users: list, save: bool = False):
    results = run.multiple(pool, users, False)
    print("results", results)
    # TODO: Add results to database


#########################
# Views endpoints
#########################


@app.route("/")
def home():
    config = get_config()
    return render_template("home.html", config=config)


@app.route("/users_list")
def users_list():
    return render_template("users_list.html")


@app.route("/add_user", methods=["GET", "POST"])
def add_user():
    if request.method == "POST":
        try:
            db_add_user(
                dni=request.form["username"],
                password=request.form["password"],
                name=request.form["name"],
            )
            flash(f"Nueva cuenta añadida [{request.form['username']}]", "info")
        except Exception:
            flash(
                f"Ya existe una cuenta con el DNI/NIE [{request.form['username']}]",
                "danger",
            )
        return redirect(url_for("home"))
    return render_template("add_user.html")


#########################
# API Endpoints
#########################


@app.route("/settings", methods=["POST", "GET"])
def settings():
    """Update cfg file from UI.

    TODO: Create a function update_config
    """
    base_path = Path(__file__).parent.parent / "scrapper"
    cfg_updated: dict = request.form.to_dict()
    cfg = get_config()
    # update current cfg
    cfg["script"]["frecuencia [minutos]"] = int(cfg_updated.pop("frecuencia [minutos]"))
    cfg["browser"]["gecko_driver"] = cfg_updated.pop("gecko_driver")

    v: str
    for k, v in cfg_updated.items():
        try:
            cfg["browser"][k] = int(v)  # timeout value
        except ValueError:
            cfg["browser"][k] = True if v == "True" else False

    with open(f"{base_path}/config.json", "w") as cfg_file:
        json.dump(cfg, cfg_file)
    flash("Configuraciones actualizadas", "info")
    return redirect(url_for("home"))


@app.route("/get_all_users", methods=["GET"])
def get_all_users():
    return User.json()


@app.route("/get_plot/<dni>", methods=["GET"])
def get_plot(dni):
    user = User.get_by_dni(dni)
    create_barchart(dni, data=UserTotalStats(user).to_dict())
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
    users: list = User.as_list()
    try:  # avoids start two jobs with same id
        pool = ThreadPool(4)
        print("Starting a new job")
        scheduler.add_job(
            **scheduler_config(sched_task, (pool, users), datetime.datetime.now())
        )
        flash("Iniciada nueva consulta automatica", "info")
    except ConflictingIdError:
        pass

    return redirect(url_for("home"))


@app.route("/stop_read")
def stop_read():
    """Stop the process of readings."""
    flash("Terminadas las consultas automatica.", "info")
    scheduler.remove_job("contador")
    return redirect(url_for("home"))


from ui.models import Read, User, UserTotalStats, db_add_user  # noqa


if __name__ == "__main__":
    app.run(debug=True)
