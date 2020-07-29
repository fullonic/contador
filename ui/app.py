import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers import (
    SchedulerNotRunningError,
    SchedulerAlreadyRunningError,
)
from flask import Flask, render_template, url_for, redirect
from multiprocessing.pool import ThreadPool
from flask_sqlalchemy import SQLAlchemy  # type: ignore
from scrapper import run


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.db"
db = SQLAlchemy(app)

scheduler = BackgroundScheduler()


def scheduler_config(fn, args, start):
    return {
        "func": fn,
        "args": args,
        "trigger": "interval",
        "minutes": 3,
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


@app.route("/read")
def read():
    pool = ThreadPool(4)
    print("Starting a new job")
    scheduler.add_job(
        **scheduler_config(run.multiple, (pool,), datetime.datetime.now())
    )

    return redirect(url_for("home"))


@app.route("/stop_read")
def stop_read():
    print("Stopping job")
    scheduler.remove_job("contador")
    return redirect(url_for("home"))


from ui.models import User, Read  # noqa

db.create_all()
if __name__ == "__main__":
    app.run(debug=True)
