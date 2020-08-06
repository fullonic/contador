import datetime

import pytest
from sqlalchemy import extract, and_, or_
import itertools

from ui.graphs import (
    generate_graphic_axis,
    generate_graphic,
    create_plot,
    create_barchart,
)
from ui.app import db
from ui.models import (
    Read,
    User,
    calculate_max_consumption_peak,
    calculate_min_consumption_peak,
    calculate_average_consumption,
    UserTotalStats,
    WeekStats,
)
from scrapper.contador import singleReadData


@pytest.fixture(scope="module")
def user():
    return User.query.get(1)


def test_get_all_user_as_dict():
    # from ui.models import User

    users_list = User.json()
    # assert isinstance(users_list, list)
    assert isinstance(users_list, dict)
    assert len(users_list["users"]) == 20


def test_generate_graphic_axis():
    # from ui.models import User

    test_dni = "E8600426D"  # pass by js query
    user = User.get_by_dni(test_dni)
    axis = generate_graphic_axis(test_dni, user.reads.all())
    isinstance(axis, tuple)
    isinstance(axis[1], tuple)
    isinstance(axis[1][0], list)


def test_generate_graphic():
    # from ui.models import User

    test_dni = "E8600426D"  # pass by js query
    user = User.get_by_dni(test_dni)
    dni, axis = generate_graphic_axis(test_dni, user.reads.all())
    graphic = generate_graphic(dni, axis)
    assert isinstance(graphic, str)
    # assert "E8600426D" in graphic


def test_create_plot():
    # from ui.models import User

    test_dni = "E8600426D"  # pass by js query
    user = User.get_by_dni(test_dni)
    create_plot(test_dni, tuple(user.reads.all()))


@pytest.mark.skip
def test_filter_query_by_data_range():
    """
    https://stackoverflow.com/questions/11616260/how-to-get-all-objects-with-a-date-that-fall-in-a-specific-month-sqlalchemy/31641488
    """
    start, end = 0, 0

    days = Read.query.filter(
        Read.user_id == 1,
        extract("month", Read.date) == 10,
        extract("month", Read.date) == 8,
    ).all()

    assert len(days) != 0


def test_query_by_consume_times(user):
    """Filter by difference times of power consumption price.

    Tests
    Read.get_hora_punta()
    Read.get_hora_llana()
    Read.get_hora_valle()

    https://stackoverflow.com/questions/51451768/sqlalchemy-querying-with-datetime-columns-to-filter-by-month-day-year/51468737
    """
    hora_punta = ((10, 14), (18, 22))  # noqa
    hora_llana = ((8, 10), (14, 18), (22, 24))  # noqa
    hora_valle = ((0, 8),)  # noqa

    # hora punta
    reads = Read.query.filter(
        Read.user_id == user.id,
        Read.weekend == False,  # noqa
        or_(
            and_(Read.date_hour >= 10, Read.date_hour <= 14),
            and_(Read.date_hour >= 18, Read.date_hour <= 22),
        ),
    ).all()

    # confirm that all hours are beetwen 10-14 or 18-22
    assert len(reads) != 0
    for el in reads:
        assert (10 <= el.date.hour and el.date.hour <= 14) or (
            18 <= el.date.hour and el.date.hour <= 22
        )
        assert el.weekend is False

    # hora llana
    reads = Read.query.filter(
        Read.user_id == user.id,
        Read.weekend == False,  # noqa
        or_(
            and_(Read.date_hour >= 8, Read.date_hour <= 10),
            and_(Read.date_hour >= 14, Read.date_hour <= 18),
            and_(Read.date_hour >= 22, Read.date_hour <= 24),
        ),
    ).all()

    assert len(reads) != 0
    for el in reads:
        assert (
            (8 <= el.date.hour and el.date.hour <= 10)
            or (14 <= el.date.hour and el.date.hour <= 18)
            or (22 <= el.date.hour and el.date.hour <= 24)
        )
        assert el.weekend is False

    # hora valle
    reads = Read.query.filter(
        Read.user_id == user.id,
        or_(Read.weekend == False, Read.weekend == True),  # noqa
        and_(Read.date_hour >= 0, Read.date_hour <= 8),
    ).all()

    assert len(reads) != 0
    for el in reads:
        assert 0 <= el.date.hour and el.date.hour <= 8
        assert (el.weekend is True) or (el.weekend is False)


def test_punta_stats():
    punta_consume = Read.get_hora_llana(1)
    max_ = calculate_max_consumption_peak(punta_consume)
    min_ = calculate_min_consumption_peak(punta_consume)
    expected = {
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
    historic_stats = Read.historic_stats(id_=1)
    assert max_ > 0
    assert min_ < max_
    assert isinstance(historic_stats, dict)
    assert expected.keys() == historic_stats.keys()


def test_user_total_stats_get_stats(user):
    total_stats = UserTotalStats(user).get_stats()
    assert isinstance(total_stats, list)
    assert isinstance(total_stats[0], WeekStats)
    assert total_stats[0].timestamp.year == 2020
    assert total_stats[0].max_valle == 5.49
    assert total_stats[0].max_punta == 5.43


def test_user_total_stats_by_week(user):
    stats = UserTotalStats(user).stats_by_week()
    assert isinstance(stats, list)
    assert isinstance(stats[0], WeekStats)
    assert isinstance(stats[0].values, itertools._grouper)
    for data in stats[0].values:
        assert isinstance(data, Read)


def test_user_total_to_dict(user):
    stats = UserTotalStats(user).to_dict()
    assert isinstance(stats, list)
    assert isinstance(stats[0], dict)


def test_create_barchart(user):
    stats = UserTotalStats(user).to_dict()
    create_barchart(user.dni, stats)


def test_add_results_into_db():
    results = [
        (
            False,
            {
                "47635719M": singleReadData(
                    date=datetime.datetime(2020, 8, 6, 19, 44, 47, 702887),
                    power=None,
                    percent=None,
                    max_power=None,
                )
            },
        ),
        (
            True,
            {
                "47635719M": singleReadData(
                    date=datetime.datetime(2020, 8, 6, 19, 44, 47, 702887),
                    power=None,
                    percent=None,
                    max_power=None,
                )
            },
        ),
    ]
    for res in results:
        if res[0] is False:
            continue
        else:
            # TODO: Add results to database
            date, power, percent, max_power = list(res[1].values())[0].to_tuple()
            print(date, power, percent, max_power)
            # breakpoint()
