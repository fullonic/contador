from ui.app import db


class User(db.Model):
    """User database model."""

    __tablename__ = "users"
    id = db.Column(db.Integer(), primary_key=True)
    dni = db.Column(db.String(255), index=True, unique=True)
    name = db.Column(db.String(255))
    password = db.Column(db.String(255))
    reads = db.relationship("Read", backref="user", lazy="dynamic")

    @classmethod
    def get_by_dni(cls, dni):
        """Query a user by it's DNI/NIE."""
        return cls.query.filter_by(dni=dni).first()

    @classmethod
    def all_reads(cls, dni):
        """Query a user by it's DNI/NIE."""
        return cls.get_by_dni(dni).reads.all()

    @classmethod
    def json(cls):
        """Return user base info as json."""
        return {
            "users": [{"dni": user.dni, "name": user.name} for user in cls.query.all()]
        }



class Read(db.Model):
    __tablename__ = "reads"
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey("users.id"))
    instantaneous_consume = db.Column(db.Float())
    percent = db.Column(db.Float())
    max_power = db.Column(db.Float())
    date = db.Column(db.DateTime())


def add_user(username, password, name):
    """Add new user to db."""
    try:
        new_user = User(dni=username, password=password, name=name)
        db.session.add(new_user)
        db.session.commit()
    except Exception as e:
        print(e)
