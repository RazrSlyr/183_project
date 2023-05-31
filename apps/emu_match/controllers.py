"""
This file defines actions, i.e. functions the URLs are mapped into
The @action(path) decorator exposed the function at URL:

    http://127.0.0.1:8000/{app_name}/{path}

If app_name == '_default' then simply

    http://127.0.0.1:8000/{path}

If path == 'index' it can be omitted:

    http://127.0.0.1:8000/

The path follows the bottlepy syntax.

@action.uses('generic.html')  indicates that the action uses the generic.html template
@action.uses(session)         indicates that the action uses the session
@action.uses(db)              indicates that the action uses the db
@action.uses(T)               indicates that the action uses the i18n & pluralization
@action.uses(auth.user)       indicates that the action requires a logged in user
@action.uses(auth)            indicates that the action requires the auth object

session, db, T, auth, and tempates are examples of Fixtures.
Warning: Fixtures MUST be declared with @action.uses({fixtures}) else your app will result in undefined behavior
"""

from py4web import action, request, abort, redirect, URL
from yatl.helpers import A
from .common import db, session, T, cache, auth, logger, authenticated, unauthenticated, flash
from py4web.utils.url_signer import URLSigner
from .models import get_user_id, get_time, get_user_email

url_signer = URLSigner(session)

@action("index")
@action.uses("index.html", auth.user, T, url_signer)
def index():
    # Put the index code here
    matchmake_url = URL("matchmaking", signer=url_signer)
    chat_url = URL("chat", signer=url_signer)
    return dict(matchmake_url=matchmake_url, chat_url=chat_url)

@action("chat")
@action.uses("chat.html", url_signer.verify()) 
def chat(): 
    get_chat_url = URL("get_chat", signer=url_signer)
    add_chat_url = URL("add_chat", signer=url_signer)
    return dict(get_chat_url=get_chat_url, add_chat_url=add_chat_url)

@action("get_chat", method="GET")
@action.uses(url_signer.verify(), db, auth.user) 
def chat():     
    chats = db(db.chat.user != -1).select().as_list()  # change this?
    return dict(chats=chats)

@action("add_chat", method="POST")
@action.uses(url_signer.verify(), db, auth.user) 
def chat():
    chat = request.params.get("chat")
    if chat == "":
        return "Error"
    else:
        db.chat.insert(user=get_user_id(), email=get_user_email(), time=get_time(), chat=chat)
        return "ok"


@action("matchmaking")
@action.uses("matchmaking.html", url_signer.verify()) 
def matchmaking():
    # Put the code for the matchmaking page here
    return dict(queue_url=URL("join_queue", signer=url_signer),
                check_url=URL("check_match", signer=url_signer))

@action("join_queue")
@action.uses(url_signer.verify())
def join_queue():
    # check if already in queue
    queue_entry = db(db.matchmaking["uid"] == get_user_id()).select().as_list()
    if (len(queue_entry) > 0):
        # Already in requeue
        return "ALREADY IN QUEUE"
    # Else, add to queue
    db.matchmaking.insert(uid=get_user_id())
    # regrab queue entry
    queue_entry = db(db.matchmaking["uid"] == get_user_id()).select().as_list()[0]
    # set "group_num" status
    id = queue_entry["id"]
    db.matchmaking[id] = dict(group_num=((id-1) // 2))
    return "OK"

@action("check_match")
@action.uses(url_signer.verify())
def check_match():
    # check for user with same group_num
    group_num = db(db.matchmaking["uid"] == get_user_id()).select().as_list()[0]["group_num"]
    matches = db(db.matchmaking["group_num"] == group_num).select().as_list()
    # check if a match was found
    if (len(matches) == 1):
        return dict(found=False)
    # grab user that isn't current user
    match = None
    for m in matches:
        if m["uid"] is not get_user_id():
            match = db.auth_user[m["uid"]]
    return dict(found=True, match=match["email"])
    