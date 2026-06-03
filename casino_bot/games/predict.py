"""Predict game — pure logic and UI builders."""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def predict_get_multiplier(selected, selection_type):
    """Calculate multiplier based on selection count with house edge"""
    if selection_type in ("even", "odd", "low", "high"):
        count = 3
    else:
        count = len(selected)
    if count == 0 or count >= 6:
        return 0.0
    raw = 6.0 / count
    mult = round(raw * (1 - PREDICT_HOUSE_EDGE), 2)
    return mult




def predict_build_message(user_id, session):
    """Build the predict game message text"""
    selected = session.get('selected', set())
    selection_type = session.get('selection_type')
    bet = session.get('bet', PREDICT_DEFAULT_BET)
    balance = get_user_balance(user_id)
    balance_usd = balance * STARS_TO_USD

    mult = predict_get_multiplier(selected, selection_type)

    # Format selected display
    if selection_type == "even":
        sel_display = "Even (2, 4, 6)"
    elif selection_type == "odd":
        sel_display = "Odd (1, 3, 5)"
    elif selection_type == "low":
        sel_display = "1-3"
    elif selection_type == "high":
        sel_display = "4-6"
    elif selected:
        sel_display = " ".join(str(n) for n in sorted(selected))
    else:
        sel_display = "None"

    bet_usd = bet * STARS_TO_USD

    text = (
        f"🎲 <b>Make a prediction for number outcomes</b>\n\n"
        f"🔵 Multiplier: <b>x{mult:.2f}</b>\n"
        f"🔥 Selected numbers: <b>{sel_display}</b>\n"
        f"💰 Bet: <b>${bet_usd:.2f}</b> ({bet} ⭐)\n"
        f"🧿 Current balance: <b>${balance_usd:.2f}</b> ({balance:,} ⭐)"
    )
    return text




def predict_build_keyboard(session, user_id=None):
    """Build the predict game inline keyboard"""
    selected = session.get('selected', set())
    selection_type = session.get('selection_type')

    def num_label(n):
        if selection_type == "even" and n % 2 == 0:
            return f"✅ {n}"
        elif selection_type == "odd" and n % 2 == 1:
            return f"✅ {n}"
        elif selection_type == "low" and n <= 3:
            return f"✅ {n}"
        elif selection_type == "high" and n >= 4:
            return f"✅ {n}"
        elif n in selected and selection_type is None:
            return f"✅ {n}"
        return str(n)

    keyboard = [
        [
            InlineKeyboardButton(num_label(1), callback_data="pred_num_1"),
            InlineKeyboardButton(num_label(2), callback_data="pred_num_2"),
            InlineKeyboardButton(num_label(3), callback_data="pred_num_3"),
        ],
        [
            InlineKeyboardButton(num_label(4), callback_data="pred_num_4"),
            InlineKeyboardButton(num_label(5), callback_data="pred_num_5"),
            InlineKeyboardButton(num_label(6), callback_data="pred_num_6"),
        ],
        [
            InlineKeyboardButton(("✅ " if selection_type == "even" else "") + t("btn_even", user_id=user_id), callback_data="pred_even"),
            InlineKeyboardButton(("✅ " if selection_type == "odd" else "") + t("btn_odd", user_id=user_id), callback_data="pred_odd"),
        ],
        [
            InlineKeyboardButton("✅ 1-3" if selection_type == "low" else "1-3", callback_data="pred_low"),
            InlineKeyboardButton("✅ 4-6" if selection_type == "high" else "4-6", callback_data="pred_high"),
        ],
        [
            InlineKeyboardButton(t("btn_play", user_id=user_id), callback_data="pred_play"),
        ],
        [
            InlineKeyboardButton(t("btn_change_bet", user_id=user_id), callback_data="pred_change_bet"),
        ],
        [
            InlineKeyboardButton(t("btn_cancel_game2", user_id=user_id), callback_data="pred_cancel"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)

