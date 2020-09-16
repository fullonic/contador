import csv
import datetime
import json
import logging
import tempfile
from multiprocessing.pool import ThreadPool
from pathlib import Path
from io import StringIO

from apscheduler.jobstores.base import ConflictingIdError  # type: ignore
from apscheduler.schedulers import SchedulerAlreadyRunningError  # type: ignore
from apscheduler.schedulers.background import BackgroundScheduler  # type: ignore
from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
    send_file,
)
from flask_sqlalchemy import SQLAlchemy  # type: ignore

from scrapper import run
from scrapper.contador import get_config
from ui.graphs import create_barchart

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SECRET_KEY"] = "only_for_local_networks"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

log = logging.getLogger("werkzeug")
log.disabled = True

db = SQLAlchemy(app)
scheduler = BackgroundScheduler()


#########################
# Helper functions
#########################
def start_reads():
    """Start the process of readings."""
    try:  # avoids start two jobs with same id
        update_status(True)
        pool = ThreadPool(4)
        print("Comenzando una nueva consulta")
        scheduler.add_job(
            **scheduler_config(sched_task, (pool,), datetime.datetime.now())
        )
    except ConflictingIdError:
        pass


def get_contador_status() -> bool:
    """Get contador running status."""
    with open("status.json") as f:
        status = json.load(f)
    return status["running"]


def update_status(status: bool):
    """Update contadtor running status based in user action."""
    with open("status.json", "w") as f:
        json.dump({"running": status}, f)


def scheduler_config(fn, args, start):
    """Scheduler base configurations."""
    return {
        "func": fn,
        "args": args,
        "trigger": "interval",
        "minutes": 15,
        "next_run_time": start,
        "id": "contador",
    }


def _csv_writer(fname):
    """CSV like text in memory writer.

    Writes a csv like object to be saved later in a tempfile to be send to the user
    """
    dni = fname.split(".")[0]
    user_records = User.all_reads(dni)
    f = StringIO()
    csv_writer = csv.writer(f)
    csv_writer.writerow(
        [
            "Consumo Instantáneo",
            "Porcentaje",
            "Potencia máxima contratada",
            "Dia",
            "Hora",
            "Fin de semana",
        ]
    )
    for rec in user_records:
        csv_writer.writerow(
            [
                rec.instantaneous_consume,
                rec.percent,
                rec.max_power,
                rec.date.strftime("%D"),  # Day
                rec.date.strftime("%T"),  # Hour
                ("Si" if rec.weekend is True else "No"),
            ]
        )
    return f


def sched_task(pool: ThreadPool, save: bool = False):
    """Schedule call to run contador script automatically on background."""

    users: list = User.as_list()  # will get new users automatically on every run
    results = run.multiple(pool, users, False)
    for res in results:
        if res[0] is False:
            continue
        else:
            # TODO: Add results to database
            add_reads(res[1])
    # TODO: Delete all csv if exist


#########################
# Views endpoints
#########################


@app.route("/")
def home():
    """Application GUI home page."""
    config = get_config()
    status = app.config["STATUS"]
    return render_template("home.html", config=config, status=status)


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


@app.route("/edit_user/<dni>", methods=["GET", "POST"])
def edit_user(dni):
    """Edit/ Delete user account."""
    if request.method == "POST":
        flash(f"Cuenta {dni} actualizada ", "success")
        # updated_user = update_user(dni, request.form.to_dict())
        # return render_template("edit_user.html", user=updated_user)
        return redirect(url_for("users_list"))
    edit_user = User.get_by_dni(dni)
    return render_template("edit_user.html", user=edit_user)


#########################
# API Endpoints
#########################
@app.route("/export_csv/<fname>")
def export_csv(fname: str):
    in_memory_csv: StringIO = _csv_writer(fname)
    with tempfile.NamedTemporaryFile("w") as f:
        f.write(in_memory_csv.getvalue())
        in_memory_csv.close()
        return send_file(f.name, attachment_filename=fname, mimetype="text/csv")


@app.route("/delete_user/<dni>", methods=["GET"])
def delete_user(dni):
    """Remove user account from db."""
    delete_user(dni)
    flash(f"Cuenta {dni} borrada", "success")
    return redirect(url_for("users_list"))


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
    cfg["browser"]["headless"] = cfg_updated.get("headless", False)
    cfg["browser"]["native_events_enabled"] = cfg_updated.get(
        "native_events_enabled", False
    )
    for k, v in cfg_updated.items():
        try:
            cfg["browser"][k] = int(v)  # timeout value
        except ValueError:
            pass

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
    """App endpoint to start reads."""
    start_reads()
    flash("Iniciada nueva consulta automatica", "info")
    return redirect(url_for("home"))


@app.route("/stop_read")
def stop_read():
    """Stop the process of readings."""
    update_status(False)
    flash("Terminadas las consultas automatica.", "info")
    scheduler.remove_job("contador")
    app.config["STATUS"]["running"] = False
    return redirect(url_for("home"))


@app.before_first_request
def start_scheduler():
    """Start scheduler but without any tasks."""
    try:
        print("Starting scheduler")
        scheduler.start()
    except SchedulerAlreadyRunningError:
        pass


from ui.models import (
    Read,
    User,
    UserTotalStats,
    add_reads,  # noqa
    db_add_user,
    delete_user,
    update_user,
)  # noqa isort:skip

db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
