from ui.app import db
from ui.graphs import generate_graphic_axis, generate_graphic, create_plot
import datetime
import pytest
from ui.models import Read, User
from sqlalchemy import extract, and_, or_
from sqlalchemy.ext.hybrid import hybrid_property


def test_get_all_user_as_dict():
    from ui.models import User

    users_list = User.json()
    # assert isinstance(users_list, list)
    assert isinstance(users_list, dict)
    assert len(users_list["users"]) == 30


def test_generate_graphic_axis():
    from ui.models import User

    test_dni = "A5961069L"  # pass by js query
    user = User.get_by_dni(test_dni)
    axis = generate_graphic_axis(test_dni, user.reads.all())
    isinstance(axis, tuple)
    isinstance(axis[1], tuple)
    isinstance(axis[1][0], list)


def test_generate_graphic():
    from ui.models import User

    test_dni = "A5961069L"  # pass by js query
    user = User.get_by_dni(test_dni)
    dni, axis = generate_graphic_axis(test_dni, user.reads.all())
    graphic = generate_graphic(dni, axis)
    assert isinstance(graphic, str)
    assert "A5961069L" in graphic


def test_create_plot():
    from ui.models import User

    test_dni = "A5961069L"  # pass by js query
    user = User.get_by_dni(test_dni)
    create_plot(test_dni, tuple(user.reads.all()))


def test_filter_query_by_data_range():
    """
    https://stackoverflow.com/questions/11616260/how-to-get-all-objects-with-a-date-that-fall-in-a-specific-month-sqlalchemy/31641488
    """
    start, end = 0, 0

    days = Read.query.filter(
        Read.user_id == 1,
        extract("month", Read.date) == 10,
        extract("month", Read.date) == 2,
    ).all()

    assert len(days) != 0


def test_query_by_consume_times():
    """Filter by difference times of power consumption price.

    Tests
    Read.get_hora_punta()
    Read.get_hora_llana()
    Read.get_hora_valle()

    https://stackoverflow.com/questions/51451768/sqlalchemy-querying-with-datetime-columns-to-filter-by-month-day-year/51468737
    """
    hora_punta = ((10, 14), (18, 22))
    hora_llana = ((8, 10), (14, 18), (22, 24))
    hora_valle = ((0, 8),)

    user = User.query.get(1)
    # hora punta
    reads = Read.query.filter(
        Read.user_id == user.id,
        or_(
            and_(Read.date_hour >= 10, Read.date_hour <= 14),
            and_(Read.date_hour >= 18, Read.date_hour <= 22),
        ),
    ).all()

    # confirm that all hours are beetwen 10-14 or 18-22
    for el in reads:
        assert (10 <= el.date.hour and el.date.hour <= 14) or (
            18 <= el.date.hour and el.date.hour <= 22
        )
        # assert (10 <= el.date.hour >= 14) and (18 <= el.date.hour >= 22)

    assert len(reads) == 8001
    # hora llana
    reads = Read.query.filter(
        Read.user_id == user.id,
        or_(
            and_(Read.date_hour >= 8, Read.date_hour <= 10),
            and_(Read.date_hour >= 14, Read.date_hour <= 18),
            and_(Read.date_hour >= 22, Read.date_hour <= 24),
        ),
    ).all()

    for el in reads:
        assert (
            (8 <= el.date.hour and el.date.hour <= 10)
            or (14 <= el.date.hour and el.date.hour <= 18)
            or (22 <= el.date.hour and el.date.hour <= 24)
        )

    # hora valle
    reads = Read.query.filter(
        Read.user_id == user.id, and_(Read.date_hour >= 0, Read.date_hour <= 8),
    ).all()

    for el in reads:
        assert 0 <= el.date.hour and el.date.hour <= 8
