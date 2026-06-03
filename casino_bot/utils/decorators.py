"""Reusable decorators for the casino bot."""
import logging
import traceback

logger = logging.getLogger(__name__)


def handle_errors(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        # Check if user is banned (allow admins and ban/unban commands)
        user_id = None
        if update.effective_user:
            user_id = update.effective_user.id
        elif update.message and update.message.from_user:
            user_id = update.message.from_user.id
        elif update.callback_query and update.callback_query.from_user:
            user_id = update.callback_query.from_user.id

        # Allow ban/unban commands to work even if admin is somehow banned
        command_name = func.__name__
        is_ban_command = command_name in ['ban_command', 'unban_command']

        # Check if user is banned (allow admins and ban/unban commands)
        if user_id and is_banned(user_id) and not is_admin(user_id) and not is_ban_command:
            return  # Silently ignore banned users

        # Check if user is frozen (block deposit, withdraw, and game commands)
        frozen_commands = [
            'deposit_command', 'withdraw_command', 'play_command',
            'dice_game', 'dart_game', 'football_game', 'basket_game', 'bowl_game',
            'mines_command', 'predict_command', 'cflip_setup_command', 'cf_command',
            'blackjack_command',  # /bj visual blackjack
        ]
        if user_id and is_frozen(user_id) and not is_admin(user_id) and command_name in frozen_commands:
            if update.message:
                await update.message.reply_html(
                    "🧊 <b>Your account is frozen.</b>\n\n"
                    "You cannot deposit, withdraw, or play until an admin unfreezes your account."
                )
            return

        try:
            return await func(update, context, *args, **kwargs)
        except BadRequest as e:
            logger.error(f"BadRequest in {func.__name__}: {e}")
            try:
                if update.message:
                    await update.message.reply_html(
                        translate_text(
                            "❌ <b>Request Error</b>\n\n"
                            "Something went wrong with your request. Please try again."
                        )
                    )
            except Exception:
                pass
        except Forbidden as e:
            logger.error(f"Forbidden in {func.__name__}: {e}")
        except NetworkError as e:
            logger.error(f"NetworkError in {func.__name__}: {e}")
            try:
                if update.message:
                    await update.message.reply_html(
                        "❌ <b>Network Error</b>\n\n"
                        "Connection issue. Please try again later."
                    )
            except Exception:
                pass
        except TelegramError as e:
            logger.error(f"TelegramError in {func.__name__}: {e}")
            try:
                if update.message:
                    msg_user_id = update.message.from_user.id if update.message.from_user else None
                    await update.message.reply_html(
                        translate_text(
                            "❌ <b>Error</b>\n\n"
                            "An error occurred. Please try again.",
                            user_id=msg_user_id
                        )
                    )
            except Exception:
                pass
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}", exc_info=True)
            try:
                if update.message:
                    msg_user_id = update.message.from_user.id if update.message.from_user else None
                    await update.message.reply_html(
                        translate_text(
                            "❌ <b>Unexpected Error</b>\n\n"
                            "Something went wrong. Please try again later.",
                            user_id=msg_user_id
                        )
                    )
            except Exception:
                pass
    return wrapper


# ==================== BONUS COMMAND ====================

def get_next_saturday():
    """Get the next Saturday at 00:00:00 (if today is Saturday, return next Saturday)"""
    now = datetime.now()
    # Saturday is weekday 5 (Monday=0, Sunday=6)
    days_until_saturday = (5 - now.weekday()) % 7

    # If today is Saturday, return next Saturday (7 days)
    if days_until_saturday == 0:
        days_until_saturday = 7

    next_saturday = now.replace(hour=0, minute=0, second=0, microsecond=0)
    next_saturday += timedelta(days=days_until_saturday)
    return next_saturday


def is_saturday():
    """Check if today is Saturday"""
    return datetime.now().weekday() == 5


def format_time_remaining(target_time):
    """Format time remaining as 'X Days HH:MM:SS'"""
    now = datetime.now()
    if target_time <= now:
        return "0 Days 00:00:00"

    delta = target_time - now
    days = delta.days
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    return f"{days} Days {hours:02d}:{minutes:02d}:{seconds:02d}"


def calculate_estimated_weekly_bonus(user_id):
    """Return a random weekly bonus amount to display (30-50 stars)."""
    return random.randint(BONUS_MIN, BONUS_MAX)


def get_weekly_bonus_amount():
    """Return a random weekly bonus amount within range."""
    return random.randint(BONUS_MIN, BONUS_MAX)


