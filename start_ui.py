"""Contador UI application starting point."""

from ui.app import app, db, start_scheduler, start_reads, get_contador_status  # noqa
from ui.models import User, Read, db_add_user  # noqa


def was_running():
    """Contador auto status check.

    In case of a electric power failure, at the next app start up, this functions checks
    if contador was running or not.
    If it was running, it will start again automatically to ensure that reads keeps on.
    """
    if get_contador_status() is True:
        start_scheduler()
        # start tasks again calling read() endpoint function
        start_reads()
    return


db.create_all()
if __name__ == "__main__":
    was_running()
    app.run(debug=True, host="0.0.0.0", port=5001)
