"""Generate fake data for dev purposes."""
import random
import secrets
from string import ascii_uppercase
import math
import datetime

from ui.app import db
from ui.models import User, Read


def get_users():
    """All users from database."""
    return User.query.all()


#########################
# Fake Users
#########################
def get_name():
    """Get a random name."""
    names = [
        "llop",
        "llorenç",
        "llucia",
        "higini",
        "hilari",
        "hipolit",
        "honest",
        "honorat",
        "honori",
        "hubert",
        "huc",
        "humbert",
        "ida",
        "ignasi",
        "igor",
        "ildefons",
        "imelda",
        "isolda",
        "iu",
        "iva",
        "ivette",
        "jacint",
        "jacinta",
        "jacob",
        "jasmina",
        "jennifer",
        "jeremies",
        "jeroni",
        "jesus",
        "joan",
        "joaquim",
        "joaquima",
        "job",
        "jonatan",
        "jorda",
        "jordi",
        "josefina",
        "josep",
        "juniper",
        "just",
        "justa",
        "justina",
        "justinia",
        "juvenal",
        "kaled",
        "kali",
        "lambert",
        "lancelot",
        "landeli",
        "lara",
        "laura",
        "laurea",
        "laurenti",
        "lavinia",
        "lea",
        "leandre",
        "leila",
        "leocadia",
        "leonci",
        "leonor",
        "leopold",
        "leovigild",
        "licini",
        "lidia",
        "lilian",
        "linus",
    ]
    return random.choice(names).title()


def generate_pass():
    """Password."""
    return secrets.token_hex()


def get_number():
    """Generate a random number from 0 to 9."""
    return str(random.randint(0, 9))


def get_letter():
    """Generate a random letter from A-Z."""
    return random.choice(ascii_uppercase)


def fake_dni(n=8):
    """Generate a spanish fake DNI."""
    dni = ""
    for _ in range(n):
        dni += get_number()
    return dni + get_letter()


def fake_nie():
    """Generate a spanish fake NIE."""
    return get_letter() + fake_dni(7)


def generate_users(n: int) -> None:
    """Generate a fake user."""
    for _ in range(n):
        u = User(
            dni=random.choice([fake_dni(), fake_nie()]),
            name=get_name(),
            password=generate_pass(),
        )
        db.session.add(u)
    db.session.commit()


#########################
# Fake Reads
#########################
def get_max_power(user=None):
    """Max contracted power."""
    if not user:
        powers = [3.3, 5.7, 4.4, 7.7]
        return random.choice(powers)
    else:
        # TODO: Get max value from user last read
        pass


def get_percent(consume, max_power):
    """Calculate percent consuption."""
    return consume / max_power * 100


def get_consume(max_power):
    """Generate instantaneous power consume."""
    return round(random.randint(1, math.floor(max_power)) - random.random(), 2)


def date_now():
    return datetime.datetime.now()


def is_weekend(dt: datetime.datetime):
    weekend_days = {6, 7}
    if dt.isoweekday() in weekend_days:
        return True
    return False


def create_first_read(users):
    for user in users:
        max_power = get_max_power()
        consume = get_consume(max_power)
        percent = get_percent(consume, max_power)
        date = date_now()
        read = Read(
            instantaneous_consume=consume,
            percent=percent,
            max_power=max_power,
            date=date,
            weekend=is_weekend(date),
            user=user,
        )
        db.session.add(read)
    db.session.commit()


def get_last_read_time(user):
    """Get last read time."""
    return user.reads.all()[-1].date


def create_fake_reads(days):
    """Generate fake read data for x days."""
    reads = days * 24 * 4  # a read for each 15 min
    users = get_users()
    create_first_read(users)
    date = get_last_read_time(users[0])
    for _ in range(reads):
        for user in users:
            max_power = user.reads.first().max_power
            consume = get_consume(max_power)
            percent = get_percent(consume, max_power)
            read = Read(
                instantaneous_consume=consume,
                percent=percent,
                max_power=max_power,
                date=date,
                weekend=is_weekend(date),
                user=user,
            )
            db.session.add(read)
        date = date + datetime.timedelta(minutes=15)
        db.session.commit()
