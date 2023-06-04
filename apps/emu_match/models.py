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


# Define your table below
#
# db.define_table('thing', Field('name'))
#
# always commit your models to avoid problems later

# RV: All games a player can queue for
db.define_table("games",
                Field("name"),
                Field("platform"))

# RV: All users who are looking for a match
db.define_table("matchmaking",
                Field("uid", "reference auth_user", default=get_user_id),
                Field("game", "reference games"))

# RV: All matched lobbies (or lobbies in the process of being matched)
db.define_table("lobbies",
                Field("user_1", "reference auth_user", default=get_user_id),
                Field("user_2", "reference auth_user"),
                Field("game", "reference games"))


db.define_table("chat",
                Field("user", "reference auth_user"),
                Field("email"),
                Field("time", default=get_time()),
                Field("chat"))

db.commit()
