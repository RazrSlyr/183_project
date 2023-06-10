"""
This file defines the database models
"""

import datetime
from .common import db, Field, auth
from pydal.validators import *

def get_user_email():
    return auth.current_user.get('email') if auth.current_user else None


def get_user_id():
    return auth.current_user.get("id") if auth.current_user else None


def get_time():
    return datetime.datetime.utcnow()



db.define_table("games",
                Field("name"),
                Field("platform"))

db.define_table("lobbies",
                Field("user_1", "reference auth_user", default=get_user_id),
                Field("user_2", "reference auth_user"),
                Field("game", "reference games"))


db.define_table("chat",
                Field("lobby_num"),
                Field("user", "reference auth_user"),
                Field("email"),
                Field("time", default=get_time()),
                Field("chat"))

db.commit()
