"""

"""

from ui.app import db
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import extract, and_, or_
from typing import List


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

    @hybrid_property
    def date_hour(self):
        return self.date.hour

    @date_hour.expression
    def date_hour(cls):
        return extract("hour", cls.date)

    @classmethod
    def history_instantaneous_consume(cls, id_, timespan=()):
        """All gross comsuptions stats."""
        user_data = Read.query.filter_by(user_id=id_).all()
        return {
            "max": calculate_max_consumption_peak(user_data),
            "min": calculate_min_consumption_peak(user_data),
            "average": calculate_average_consumption(user_data),
        }

    @classmethod
    def get_hora_punta(cls, id_: int) -> List[object]:
        """Filter by hora punta.

        10 - 14 and 18 - 22
        """
        return Read.query.filter(
            Read.user_id == id_,
            or_(
                and_(Read.date_hour >= 10, Read.date_hour <= 14),
                and_(Read.date_hour >= 18, Read.date_hour <= 22),
            ),
        ).all()

    @classmethod
    def get_hora_llana(cls, id_: int) -> List[object]:
        """Filter by hora llana.

        8 - 10, 14 - 18, 22 - 24
        """
        return Read.query.filter(
            Read.user_id == id_,
            or_(
                and_(Read.date_hour >= 8, Read.date_hour <= 10),
                and_(Read.date_hour >= 14, Read.date_hour <= 18),
                and_(Read.date_hour >= 22, Read.date_hour <= 24),
            ),
        ).all()

    @classmethod
    def get_hora_valle(cls, id_: int) -> List[object]:
        """Filter by hora valle.

        0 - 8
        """
        return Read.query.filter(
            Read.user_id == id_, and_(Read.date_hour >= 0, Read.date_hour <= 8),
        ).all()


#########################
# Helper functions
#########################
def add_user(username, password, name):
    """Add new user to db."""
    try:
        new_user = User(dni=username, password=password, name=name)
        db.session.add(new_user)
        db.session.commit()
    except Exception as e:
        print(e)


def calculate_max_consumption_peak(data: list):
    """Max consumption peak."""
    return max(row.instantaneous_consume for row in data)


def calculate_min_consumption_peak(data: list):
    """Min consumption peak."""
    return min(row.instantaneous_consume for row in data)


def calculate_average_consumption(data: list):
    """Average consumption."""
    return sum(row.instantaneous_consume for row in data) / len(data)
