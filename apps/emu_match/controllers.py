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
from py4web.utils.form import Form, FormStyleBulma

url_signer = URLSigner(session)


@action("index")
@action.uses("index.html", auth, T, url_signer)
def index():
    # Put the index code here
    matchmake_url = URL("matchmaking", signer=url_signer)
    chat_url = URL("chat", signer=url_signer)
    return dict(matchmake_url=matchmake_url, chat_url=chat_url, url_signer=url_signer)


@action("chat")
@action.uses("chat.html", url_signer.verify()) 
def chat(): 
    get_chat_url = URL("get_chat", signer=url_signer)
    add_chat_url = URL("add_chat", signer=url_signer)
    return dict(get_chat_url=get_chat_url, add_chat_url=add_chat_url)

@action("get_chat", method="GET")
@action.uses(db, auth.user, url_signer.verify()) 
def get_chat():     
    chats = db(db.chat.user != -1).select().as_list()  # change this?
    return dict(chats=chats)

@action("add_chat", method="POST")
@action.uses(db, auth.user, url_signer.verify()) 
def add_chat():
    chat = request.params.get("chat")
    if chat == "":
        return "Error"
    else:
        db.chat.insert(user=get_user_id(), email=get_user_email(), time=get_time(), chat=chat)
        return "ok"



@action("matchmaking/<game_id:int>")
@action.uses("matchmaking.html", auth.user, url_signer.verify())
def matchmaking(game_id):
    # Put the code for the matchmaking page here
    print(game_id)
    return dict(queue_url=URL("join_queue", game_id, signer=url_signer),
                check_url=URL("check_match", game_id, signer=url_signer))


@action("join_queue/<game_id:int>")
@action.uses(url_signer.verify())
def join_queue(game_id):
    # RV: check if already in queue
    queue_entry = db(db.matchmaking["uid"] == get_user_id()).select().as_list()
    if (len(queue_entry) > 0):
        # RV: Already in requeue
        return "ALREADY IN QUEUE"
    # RV: Else, add to queue
    db.matchmaking.insert(uid=get_user_id(),
                          game=game_id)
    return "OK"


@action("check_match/<game_id:int>")
@action.uses(url_signer, url_signer.verify())
def check_match(game_id):
    # RV: Check if there are any lobbies for this game
    all_lobbies = db(db.lobbies["game"] == game_id).select()
    if len(all_lobbies) == 0:
        # RV: Make a lobby for this game and check again
        db.lobbies.insert(game=game_id)
        return check_match(game_id)
    # RV: Check if you're already in a lobby
    my_lobbies = db(((db.lobbies["user_1"] == get_user_id()) | (
        db.lobbies["user_2"] == get_user_id())) & (db.lobbies["game"] == game_id)).select().as_list()
    if len(my_lobbies) > 0:
        # RV: If so, check if the other user is in there
        lobby = my_lobbies[0]
        if lobby["user_1"] == get_user_id():
            # RV: user 1 is current user, check if user 2 is there
            if lobby["user_2"] != None:
                return dict(found=True, url=URL("lobby", lobby["id"], 1, signer=url_signer))
            else:
                # RV: No one, try again bozo
                return dict(found=False)
        else:
            # RV: If you are user 2, there must be user 1
            return dict(found=True, url=URL("lobby", lobby["id"], 2, signer=url_signer))

    # RV: Check for lobbies where there is a first user but no second user
    open_lobbies = db((db.lobbies["game"] == game_id) & (
        (db.lobbies["user_1"] != None) | (db.lobbies["user_2"] == None))).select().as_list()
    if len(open_lobbies) > 0:
        # RV: Grab first open lobby and add user at user 2
        lobby = open_lobbies[0]
        db.lobbies[lobby["id"]] = dict(user_2=get_user_id())
        return check_match(game_id)
    
    # RV: No lobbies that work here, make a new lobby
    # RV: Make a lobby for this game and check again
    db.lobbies.insert(game=game_id)
    return check_match(game_id)


@action("games")
@action.uses("games.html", auth.user, url_signer)
def games():
    # RV: Defines games page
    games = db(db.games).select().as_list()
    print(games)
    return dict(games=games, url_signer=url_signer)


@action("add_game", method=["GET", "POST"])
@action.uses("add_game.html", auth.user, url_signer.verify())
def add_game():
    # RV: Defines form for adding new games
    form = Form(db.games, formstyle=FormStyleBulma)
    if form.accepted:
        redirect(URL("games"))
    return dict(form=form)


@action("lobby/<lobby_num:int>/<user_num:int>")
@action.uses("lobby.html", auth.user, url_signer, url_signer.verify())
def lobby(lobby_num, user_num):
    # RV: Get lobby info name
    lobby_info = db(db.lobbies.id == lobby_num).select().as_list()
    # RV: Does this lobby still exist?
    if len(lobby_info) == 0:
        # RV: Go back to index
        redirect(URL("games"))
    lobby_info = lobby_info[0]
    # RV: Get game name and opponent name
    game_info = db(db.games.id == lobby_info["game"]).select().as_list()[0]
    game_name = game_info["name"]
    # RV: Get opp id
    opp_id = None
    if user_num == 1:
        # RV: Get user 2
        opp_id = lobby_info["user_2"]
    else:
        # RV: Get user 1
        opp_id = lobby_info["user_1"]
    
    opp_info = db(db.auth_user.id == opp_id).select().as_list()[0]
    opp_name = opp_info["email"]
    return dict(game_name=game_name, opponent=opp_name)
