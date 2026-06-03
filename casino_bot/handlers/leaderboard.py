"""Leaderboard handler — /leaderboard command and lb_* callbacks."""
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ContextTypes
from telegram.constants import ParseMode


# Import leaderboard data from config
try:
    from casino_bot.config import LEADERBOARD_DATA, LEADERBOARD_IMAGES
except ImportError:
    LEADERBOARD_DATA = {}
    LEADERBOARD_IMAGES = {}


def build_lb_caption(category):
    """Build a formatted leaderboard caption for the given category."""
    data = LEADERBOARD_DATA.get(category, {})
    if not data:
        return "No data available."
    lines = [f"<b>{data['title']}</b>\n"]
    for rank, name, value in data.get("entries", []):
        lines.append(f"{rank} <b>{name}</b> — {value}")
    return "\n".join(lines)


def build_lb_keyboard():
    """Build the 2x2 inline keyboard for leaderboard categories."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🏆 Most Wins", callback_data="lb_wins"),
            InlineKeyboardButton("💰 Most Money Won", callback_data="lb_money"),
        ],
        [
            InlineKeyboardButton("🎮 Most Active", callback_data="lb_active"),
            InlineKeyboardButton("🎲 Highest Roller", callback_data="lb_roller"),
        ],
    ])


async def handle_lb_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle leaderboard category switch callbacks."""
    query = update.callback_query
    cat_key = query.data.replace("lb_", "")
    if cat_key not in LEADERBOARD_DATA:
        await query.answer("Unknown category")
        return
    await query.answer()
    caption = build_lb_caption(cat_key)
    markup = build_lb_keyboard()
    try:
        img_path = LEADERBOARD_IMAGES.get(cat_key)
        if img_path and os.path.exists(img_path):
            with open(img_path, "rb") as img:
                media = InputMediaPhoto(media=img, caption=caption, parse_mode=ParseMode.HTML)
                await query.edit_message_media(media=media, reply_markup=markup)
        else:
            await query.edit_message_caption(
                caption=caption, reply_markup=markup, parse_mode=ParseMode.HTML
            )
    except Exception:
        pass
