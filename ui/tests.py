from .app import db
from ui.models import User
import pytest


def test_get_all_user_as_dict():
    users_list = User.json()
    # assert isinstance(users_list, list)
    assert isinstance(users_list, dict)
    assert len(users_list["users"]) == 30
