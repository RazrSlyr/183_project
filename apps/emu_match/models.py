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



# RV: All games a player can queue for
db.define_table("games",
                Field("name"),
                Field("platform"))

# RV: All matched lobbies (or lobbies in the process of being matched)
db.define_table("lobbies",
                Field("user_1", "reference auth_user", default=get_user_id),
                Field("user_2", "reference auth_user"),
                Field("game", "reference games"))


# MP: All chats seperated by lobby_num
db.define_table("chat",
                Field("lobby_num"),
                Field("user", "reference auth_user"),
                Field("email"),
                Field("time", default=get_time()),
                Field("likes", "integer", default=0),
                Field("chat"))




db.commit()
