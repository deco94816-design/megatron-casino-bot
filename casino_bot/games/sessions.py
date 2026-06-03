"""Centralized game session management."""

# ── Game session stores ──
game_sessions = {}        # Dice/dart/bowl/football/basketball
coinflip_sessions = {}    # Coinflip games
predict_sessions = {}     # Predict games
blackjack_sessions = {}   # Blackjack games
mines_games = {}          # Mines games


def get_game_session(user_id):
    return game_sessions.get(user_id)

def create_game_session(user_id, data):
    game_sessions[user_id] = data
    return data

def end_game_session(user_id):
    return game_sessions.pop(user_id, None)

def get_bj_session(user_id):
    return blackjack_sessions.get(user_id)

def create_bj_session(user_id, data):
    blackjack_sessions[user_id] = data
    return data

def end_bj_session(user_id):
    return blackjack_sessions.pop(user_id, None)

def get_predict_session(user_id):
    return predict_sessions.get(user_id)

def create_predict_session(user_id, data):
    predict_sessions[user_id] = data
    return data

def end_predict_session(user_id):
    return predict_sessions.pop(user_id, None)

def get_cf_session(user_id):
    return coinflip_sessions.get(user_id)

def create_cf_session(user_id, data):
    coinflip_sessions[user_id] = data
    return data

def end_cf_session(user_id):
    return coinflip_sessions.pop(user_id, None)

def get_mines_game(user_id):
    return mines_games.get(user_id)

def create_mines_game(user_id, data):
    mines_games[user_id] = data
    return data

def end_mines_game(user_id):
    return mines_games.pop(user_id, None)
