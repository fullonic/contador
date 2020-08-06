from ui.app import app, db
from ui.models import User, Read, db_add_user


db.create_all()
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
