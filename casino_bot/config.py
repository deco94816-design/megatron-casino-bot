"""Casino Bot Configuration — all constants and settings."""
import os

BOT_TOKEN = "8062106287:AAHuFUn04LihAfyvF8mRCAz7lg_BJRZECCg".strip()
ADMIN_ID = 5709159932
BOT_USERNAME = "Librate"
BOT_DB = "bot_data.db"  # SQLite database (fresh start)
DATA_FILE = "bot_data.json"  # JSON data file
admin_list = {ADMIN_ID, 8311802199}
ADMIN_BALANCE = 9999999999
TEMPLATES_DB = "templates.db"
EMOJI_DB = "emoji_mappings.db"
STARS_TO_USD = 0.0179
STARS_TO_TON = 0.01201014
COINFLIP_STICKERS_FILE = "coinflip_stickers.json"
CF_MULTIPLIER = 1.92
PREDICT_HOUSE_EDGE = 0.05
PREDICT_DEFAULT_BET = 10
PREDICT_MIN_BET = 1

GAME_CONFIG = {
    "dice": {
        "emoji": "🎲",
        "name": "Dice game",
        "action": "roll",
        "min": 1,
        "max": 6,
        "tg_emoji": "🎲"
    },
    "dart": {
        "emoji": "🎯",
        "name": "Dart game",
        "action": "throw",
        "min": 1,
        "max": 6,
        "tg_emoji": "🎯"
    },
    "football": {
        "emoji": "⚽",
        "name": "Football game",
        "action": "kick",
        "min": 1,
        "max": 5,
        "tg_emoji": "⚽"
    },
    "basket": {
        "emoji": "🏀",
        "name": "Basket game",
        "action": "shot",
        "min": 1,
        "max": 5,
        "tg_emoji": "🏀"
    },
    "bowl": {
        "emoji": "🎳",
        "name": "Bowling game",
        "action": "score",
        "min": 0,
        "max": 6,
        "tg_emoji": "🎳"
    }
}

MULTIPLIERS = {
    "normal": 1.92,
    "double": 1.92,
    "crazy": 1.92
}
BJ_SUITS = ["♠", "♣", "♥", "♦"]
BJ_VALUES = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]

# ── Leaderboard Data ──
LEADERBOARD_DATA = {
    "wins": {
        "title": "🏆 Most Wins",
        "entries": [
            ("🥇", "@zo_Yuji", "550 wins"),
            ("🥈", "@strut", "358 wins"),
            ("🥉", "?", "349 wins"),
            ("4.", "@sanixhhhhh", "307 wins"),
            ("5.", "@Agentplugz", "258 wins"),
            ("6.", "@Temporarilyuser", "251 wins"),
            ("7.", "@nawaz", "238 wins"),
            ("8.", "@simpstonate", "227 wins"),
        ]
    },
    "money": {
        "title": "💰 Most Money Won",
        "entries": [
            ("🥇", "@bnbsolxrpbtc", "$93,805"),
            ("🥈", "@nine", "$50,060"),
            ("🥉", "@frog", "$47,997"),
            ("4.", "@strut", "$43,394"),
            ("5.", "@OGUfed", "$40,070"),
            ("6.", "@qqqqqqqqqqqqq1237", "$25,529"),
            ("7.", "?", "$24,401"),
            ("8.", "@nawaz", "$19,886"),
        ]
    },
    "active": {
        "title": "🎮 Most Active",
        "entries": [
            ("🥇", "@zo_Yuji", "941 games"),
            ("🥈", "?", "737 games"),
            ("🥉", "@strut", "680 games"),
            ("4.", "@sanixhhhhh", "602 games"),
            ("5.", "@Agentplugz", "496 games"),
            ("6.", "@Temporarilyuser", "468 games"),
            ("7.", "@nawaz", "457 games"),
            ("8.", "@OGUfed", "442 games"),
        ]
    },
    "roller": {
        "title": "🎲 Highest Roller",
        "entries": [
            ("🥇", "@bnbsolxrpbtc", "$95,545"),
            ("🥈", "@nine", "$63,383"),
            ("🥉", "@frog", "$51,276"),
            ("4.", "@OGUfed", "$43,891"),
            ("5.", "@niiigggaaaaa", "$38,687"),
            ("6.", "@qqqqqqqqqqq4237", "$34,210"),
            ("7.", "?", "$27,770"),
            ("8.", "@NoHelm", "$20,490"),
        ]
    },
}

_LB_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LEADERBOARD_IMAGES = {
    "wins": os.path.join(_LB_DIR, "lb_wins.jpg"),
    "money": os.path.join(_LB_DIR, "lb_money.png"),
    "active": os.path.join(_LB_DIR, "lb_active.jpg"),
    "roller": os.path.join(_LB_DIR, "lb_roller.jpg"),
}
