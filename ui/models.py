"""

"""
import datetime
from itertools import groupby
from typing import List, NamedTuple, Iterator
from dataclasses import dataclass, field
import itertools
import sqlite3

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

    @classmethod
    def as_list(cls):
        """Return a list of all users in a dict format to be consumed by the contador script."""
        return [
            {"username": user.dni, "password": user.password}
            for user in cls.query.all()
        ]


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
    def stats_by_week(cls, id_):
        """TODO: Stats to be pass into create_plot."""

        def grouper(item):
            year, week, _ = item.date.isocalendar()
            return (year, week, item.date.month)

        query = cls.query.filter_by(user_id=id_).all()
        groups = [
            ((year, week, month), data)
            for ((year, week, month), data) in groupby(query, grouper)
        ]

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


@dataclass
class singleReadData:
    """TODO: Implement Results to have this format."""

    date: datetime.datetime
    power: float
    percent: float
    max_power: float


class Timestamp(NamedTuple):
    """Read date time."""

    year: int
    week: int
    month: int


@dataclass
class WeekStats:
    """Weekly reads stats."""

    timestamp: Timestamp
    values: itertools._grouper
    max_punta: float = 0.0
    max_valle: float = 0.0
    max_llana: float = 0.0


@dataclass
class UserTotalStats:
    """User historic statistics."""

    user: User
    stats: List[WeekStats] = field(default_factory=list)

    def to_dict(self):
        return [
            {
                "year": el.timestamp.year,
                "week": el.timestamp.week,
                "month": el.timestamp.month,
                "max_punta": el.max_punta,
                "max_valle": el.max_valle,
                "max_llana": el.max_llana,
            }
            for el in self.get_stats()
        ]

    def stats_by_week(self) -> List[WeekStats]:
        """TODO: Stats to be pass into create_plot."""

        def grouper(item):
            year, week, _ = item.date.isocalendar()
            return Timestamp(year, week, item.date.month)

        data = self.user.reads.all()
        ts: Timestamp
        for (ts, values) in groupby(data, grouper):
            val1, val2, val3 = itertools.tee(values, 3)
            max_valle = calculate_max_consumption_peak(self.hora_valle(val1))
            max_punta = calculate_max_consumption_peak(self.hora_punta(val2))
            max_llana = calculate_max_consumption_peak(self.hora_llana(val3))
            self.stats.append(
                WeekStats(
                    ts,
                    values=values,
                    max_valle=max_valle,
                    max_punta=max_punta,
                    max_llana=max_llana,
                )
            )
        return self.stats

    def hora_valle(self, gen):
        return [
            el
            for el in gen
            if (
                (el.date.hour >= 0)
                and (el.date.hour <= 8)
                and ((el.weekend is True) or (el.weekend is False))
            )
        ]

    def hora_punta(self, gen):
        lst = []
        for el in gen:
            if (
                (10 <= el.date.hour and el.date.hour <= 14)
                or (18 <= el.date.hour and el.date.hour <= 22)
                and el.weekend is False
            ):
                lst.append(el)
        return lst

    def hora_llana(self, gen):
        # breakpoint()
        lst2 = []
        for el in gen:
            if (
                any(
                    [
                        (8 < el.date.hour and el.date.hour < 10),
                        (14 < el.date.hour and el.date.hour < 18),
                        (22 < el.date.hour and el.date.hour < 24),
                    ]
                )
                and el.weekend is False
            ):
                # if not el.weekend:
                lst2.append(el)

        return lst2

    def get_stats(self):
        return self.stats_by_week()


#########################
# Helper functions
#########################
def db_add_user(dni, password, name):
    """Add new user to db."""

    try:
        new_user = User(dni=dni, password=password, name=name)
        db.session.add(new_user)
        db.session.commit()
        return True
    except sqlite3.IntegrityError:
        raise Exception(f"Ya existe una cuenta con el DNI/NIE [{dni}] ")


def calculate_max_consumption_peak(data: list):
    """Max consumption peak."""
    try:
        return max(row.instantaneous_consume for row in data)
    except ValueError:  # data is empty
        return


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
