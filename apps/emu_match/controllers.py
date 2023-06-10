from py4web import action, request, abort, redirect, URL
from yatl.helpers import A
from .common import db, session, T, cache, auth, logger, authenticated, unauthenticated, flash
from py4web.utils.url_signer import URLSigner
from .models import get_user_id, get_time, get_user_email
from py4web.utils.form import Form, FormStyleBulma

url_signer = URLSigner(session)


@action("index")
@action.uses("index.html", auth, url_signer)
def index():    
    matchmake_url = URL("matchmaking", signer=url_signer)
    chat_url = URL("chat", signer=url_signer)
    return dict(matchmake_url=matchmake_url, chat_url=chat_url, url_signer=url_signer)


# MP: Generate urls for general chat
@action("general_chat") 
@action.uses("general_chat.html", url_signer.verify())
def general_chat(): 
    lobby_num = "0" # MP: Ids for other lobbies start at 1
    get_chat_url = URL("get_chat", lobby_num,  signer=url_signer)
    add_chat_url = URL("add_chat", lobby_num,  signer=url_signer)
    like_chat_url = URL("like_chat")
    return dict(get_chat_url=get_chat_url, add_chat_url=add_chat_url, lobby_num=lobby_num, 
                like_chat_url=like_chat_url)

# MP: Get chats for current lobby
@action("get_chat/<lobby_num:int>", method="GET")
@action.uses(db, auth.user, url_signer.verify()) 
def get_chat(lobby_num):         
    chats = db(db.chat.lobby_num == lobby_num).select().as_list()
    return dict(chats=chats)

# MP: Add new chat
@action("add_chat/<lobby_num:int>", method="POST")
@action.uses(db, auth.user, url_signer.verify()) 
def add_chat(lobby_num):
    chat = request.params.get("chat")
    if chat == "":
        return "Error"
    else:
        db.chat.insert(lobby_num=lobby_num, user=get_user_id(), email=get_user_email(), time=get_time(), chat=chat)
        return "ok"



@action("matchmaking/<game_id:int>")
@action.uses("matchmaking.html", auth.user, url_signer.verify())
def matchmaking(game_id):
    # Put the code for the matchmaking page here
    print(game_id)
    return dict(leave_url=URL("leave_queue", game_id, signer=url_signer),
                check_url=URL("check_match", game_id, signer=url_signer))


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

@action("leave_queue/<game_id:int>")
@action.uses(url_signer, url_signer.verify())
def leave_match(game_id):
    # RV: Check if you're already in a lobby
    my_lobbies = db(((db.lobbies["user_1"] == get_user_id()) | (
        db.lobbies["user_2"] == get_user_id())) & (db.lobbies["game"] == game_id)).select().as_list()
    if len(my_lobbies) > 0:
        # RV: If so, check if the other user is in there
        lobby = my_lobbies[0]
        if lobby["user_1"] == get_user_id():
            # RV: user 1 is current user, check if user 2 is there
            if lobby["user_2"] != None:
                # RV: If there is a user 2, then you are in a lobby not queue
                # RV: You would need to use the close lobby function
                return dict(message="OK", url=URL("games"))
                
            else:
                # RV: Delete this lobby
                del db.lobbies[lobby["id"]]
                return dict(message="OK", url=URL("games"))
        else:
            # RV: If you are user 2, there must be user 1
            # RV: This means you are already in a lobby and must use close lobby
            return dict(message="OK", url=URL("games"))            

    # RV: Check for lobbies where there is a first user but no second user
    open_lobbies = db((db.lobbies["game"] == game_id) & (
        (db.lobbies["user_1"] != None) | (db.lobbies["user_2"] == None))).select().as_list()
    if len(open_lobbies) > 0:
        # RV: Grab first open lobby and add user at user 2
        lobby = open_lobbies[0]
        db.lobbies[lobby["id"]] = dict(user_2=get_user_id())
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
    
    # RV: Get information aobut opponent
    opp_info = db(db.auth_user.id == opp_id).select().as_list()[0]
    opp_name = opp_info["email"]

    get_chat_url = URL("get_chat", lobby_num, signer=url_signer)
    add_chat_url = URL("add_chat", lobby_num, signer=url_signer)
    close_lobby_url = URL("close_lobby", lobby_num, signer=url_signer)
    check_lobby_url = URL("check_lobby", lobby_num, signer=url_signer)
    like_chat_url = URL("like_chat")

    return dict(game_name=game_name, opponent=opp_name, get_chat_url=get_chat_url, add_chat_url=add_chat_url, lobby_num=lobby_num,
                close_lobby_url=close_lobby_url, check_lobby_url=check_lobby_url, like_chat_url=like_chat_url)

@action("close_lobby/<lobby_num:int>")
@action.uses(url_signer.verify())
def close_lobby(lobby_num):
    # RV: Close the lobby and chatroom
    lobby = db(db.lobbies.id == lobby_num).select().as_list()
    if (len(lobby) == 0):
        # RV: Lobby has been closed already
        return dict(message="Victory!", url=URL("games"))
    else:
        # RV: Delete the lobby
        del db.lobbies[lobby[0]["id"]]
        return dict(message="Defeat!", url=URL("games"))

@action("check_lobby/<lobby_num:int>")
@action.uses(url_signer.verify())
def check_lobby(lobby_num):
    # RV: Check if lobby exists
    lobby = db(db.lobbies.id == lobby_num).select().as_list()
    if (len(lobby) == 0):
        return dict(message="Victoy!", url=URL("games"))
    # RV: Lobby is fine
    return dict(message="OK")

@action("like_chat/<chat_id:int>")
def like_chat(chat_id):
    chat = db(db.chat.id == chat_id).select().as_list()
    if (len(chat) == 0):
        # RV: Chat either doesn't exist or doesn't belong to the user
        return dict(message="Failed")
    # RV: Update likes counter
    db.chat[chat_id] = dict(likes=(db.chat[chat_id].likes + 1))
    return dict(message="OK")
    
