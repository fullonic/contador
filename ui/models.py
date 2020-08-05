"""

"""
import datetime
from itertools import groupby
from typing import List

from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import extract, and_, or_

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
    weekend = db.Column(db.Boolean(), default=False)

    @hybrid_property
    def date_hour(self):
        return self.date.hour

    @date_hour.expression
    def date_hour(cls):
        return extract("hour", cls.date)

    @classmethod
    def historic_stats(cls, id_):
        """All gross comsuptions stats."""
        user_data = cls.query.filter_by(user_id=id_).all()
        punta = cls.get_hora_punta(id_)
        valle = cls.get_hora_valle(id_)
        llana = cls.get_hora_llana(id_)
        # breakpoint()
        # TODO: Fix ValueError when user don't have records
        try:
            return {
                "max": calculate_max_consumption_peak(user_data),
                "min": calculate_min_consumption_peak(user_data),
                "average": calculate_average_consumption(user_data),
                "max_punta": calculate_max_consumption_peak(punta),
                "min_punta": calculate_min_consumption_peak(punta),
                "average_punta": calculate_average_consumption(punta),
                "max_valle": calculate_max_consumption_peak(valle),
                "min_valle": calculate_min_consumption_peak(valle),
                "average_valle": calculate_average_consumption(valle),
                "max_llana": calculate_max_consumption_peak(llana),
                "min_llana": calculate_min_consumption_peak(llana),
                "average_llana": calculate_average_consumption(llana),
            }
        except ValueError:  # no data to be calculate max and min
            return {
                "max": "",
                "min": "",
                "average": "",
                "max_punta": "",
                "min_punta": "",
                "average_punta": "",
                "max_valle": "",
                "min_valle": "",
                "average_valle": "",
                "max_llana": "",
                "min_llana": "",
                "average_llana": "",
            }

    @classmethod
    def stats_by_month(cls, id_):
        """TODO: Stats to be pass into create_plot."""

        def grouper(item):
            return (item.date.year, item.date.month)

        query = cls.query.filter_by(user_id=id_).all()
        groups = [
            ((year, month), data) for ((year, month), data) in groupby(query, grouper)
        ]
        # for ((year, month), items) in groupby(query, grouper):
        # print(month, year, max(item.instantaneous_consume for item in items))

    @classmethod
    def get_hora_punta(cls, id_: int) -> List[object]:
        """Filter by hora punta.

        10 - 14 and 18 - 22
        """
        return Read.query.filter(
            Read.user_id == id_,
            Read.weekend == False,  # noqa
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
            Read.weekend == False,  # noqa
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
            Read.user_id == id_,
            or_(Read.weekend == False, Read.weekend == True),  # noqa
            and_(Read.date_hour >= 0, Read.date_hour <= 8),
        ).all()


#########################
# Helper functions
#########################
def db_add_user(dni, password, name):
    """Add new user to db."""
    try:
        new_user = User(dni=dni, password=password, name=name)
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


def is_weekend(dt: datetime.datetime):
    weekend_days = {6, 7}
    if dt.isoweekday() in weekend_days:
        return True
    return False
