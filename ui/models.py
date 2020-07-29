from .app import db


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer(), primary_key=True)
    dni = db.Column(db.String(255), index=True, unique=True)
    name = db.Column(db.String(255))
    password = db.Column(db.String(255))
    reads = db.relationship("Read", backref="user", lazy="dynamic")


class Read(db.Model):
    __tablename__ = "reads"
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey("users.id"))
    instantaneous_consume = db.Column(db.Float())
    percent = db.Column(db.Float())
    max_power = db.Column(db.Float())
    date = db.Column(db.DateTime())

