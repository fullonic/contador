from ui.app import db
from ui.graphs import generate_graphic_axis, generate_graphic, create_plot
import pytest


def test_get_all_user_as_dict():
    from ui.models import User
    users_list = User.json()
    # assert isinstance(users_list, list)
    assert isinstance(users_list, dict)
    assert len(users_list["users"]) == 30

def test_generate_graphic_axis():
    from ui.models import User
    test_dni = "A5961069L" # pass by js query
    user = User.get_by_dni(test_dni)
    axis = generate_graphic_axis(test_dni, user.reads.all())
    isinstance(axis, tuple)
    isinstance(axis[1], tuple)
    isinstance(axis[1][0], list)

def test_generate_graphic():
    from ui.models import User
    test_dni = "A5961069L" # pass by js query
    user = User.get_by_dni(test_dni)
    dni, axis = generate_graphic_axis(test_dni, user.reads.all())
    graphic = generate_graphic(dni, axis)
    assert isinstance(graphic, str)
    assert "A5961069L" in graphic


def test_create_plot():
    from ui.models import User
    test_dni = "A5961069L" # pass by js query
    user = User.get_by_dni(test_dni)
    create_plot(test_dni, tuple(user.reads.all()))