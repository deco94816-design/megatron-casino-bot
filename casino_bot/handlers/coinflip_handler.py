from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ContextTypes
import json
import random
from datetime import datetime

import bot
from storage import db
from casino_bot.translations import t
from casino_bot.config import STARS_TO_USD, CF_MULTIPLIER

async def handle_coinflip_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = query.from_user.id
    if data in ("cf_heads", "cf_tails"):
        call = "heads" if data == "cf_heads" else "tails"
        bet_amount = context.user_data.get('cf_bet', 0)
        if bet_amount <= 0:
            await query.answer(t("err_invalid_bet", user_id=user_id), show_alert=True)
            return

        bet_usd = bet_amount * STARS_TO_USD
        payout_usd = bet_usd * CF_MULTIPLIER

        context.user_data['cf_call'] = call
        call_display = "Heads" if call == "heads" else "Tails"

        keyboard = [
            [
                InlineKeyboardButton(t("btn_confirm", user_id=user_id), callback_data="cf_confirm"),
                InlineKeyboardButton(t("btn_cancel", user_id=user_id), callback_data="cf_cancel"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            f"You're about to start a Coinflip Game!\n\n"
            f"<b>Call:</b> {call_display}\n"
            f"<b>Bet:</b> ${bet_usd:.2f}\n"
            f"<b>Payout:</b> ${payout_usd:.2f} {CF_MULTIPLIER}x",
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
        return

    if data == "cf_confirm":
        bet_amount = context.user_data.get('cf_bet', 0)
        call = context.user_data.get('cf_call', 'heads')
        if bet_amount <= 0:
            await query.answer(t("err_invalid_bet", user_id=user_id), show_alert=True)
            return

        balance = get_user_balance(user_id)
        if balance < bet_amount:
            await query.edit_message_text(t("insufficient_balance", user_id=user_id), parse_mode=ParseMode.HTML)
            return

        if user_id in coinflip_sessions:
            await query.answer(t("err_active_coinflip", user_id=user_id), show_alert=True)
            return

        # Deduct bet
        adjust_user_balance(user_id, -bet_amount, game=True)
        user_balances[user_id] = get_user_balance(user_id)

        coinflip_sessions[user_id] = {
            "call": call,
            "bet": bet_amount,
            "chat_id": query.message.chat_id,
            "message_id": query.message.message_id,
        }

        bet_usd = bet_amount * STARS_TO_USD
        payout_usd = bet_usd * CF_MULTIPLIER
        call_display = "Heads" if call == "heads" else "Tails"

        keyboard = [[InlineKeyboardButton(t("btn_flip_coin", user_id=user_id), callback_data="cf_flip")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            f"🤖 <b>Coinflip vs Bot</b>\n\n"
            f"<b>Your call:</b> {call_display}\n"
            f"<b>Bet:</b> ${bet_usd:.2f}\n"
            f"<b>Payout:</b> ${payout_usd:.2f} ({CF_MULTIPLIER}x)\n\n"
            f"Click to flip the coin!",
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
        return

    if data == "cf_flip":
        session = coinflip_sessions.get(user_id)
        if not session:
            await query.answer(t("err_no_active_coinflip", user_id=user_id), show_alert=True)
            return

        chat_id = session['chat_id']
        bet_amount = session['bet']
        call = session['call']
        bet_usd = bet_amount * STARS_TO_USD
        payout_usd = bet_usd * CF_MULTIPLIER

        # Remove flip button
        await query.edit_message_reply_markup(reply_markup=None)

        # Random outcome
        outcome = random.choice(["heads", "tails"])
        outcome_display = "Heads" if outcome == "heads" else "Tails"

        # Send sticker (fallback to text if stickers are not configured)
        sticker_id = coinflip_stickers.get(outcome)
        if sticker_id:
            await context.bot.send_sticker(chat_id=chat_id, sticker=sticker_id)
            await asyncio.sleep(2)
        else:
            fallback_face = "🙂" if outcome == "heads" else "🪙"
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"Coin result: {fallback_face} <b>{outcome_display}</b>",
                parse_mode=ParseMode.HTML
            )
            await asyncio.sleep(1)

        # Get user display
        profile = get_or_create_profile(user_id)
        display_name = profile.get('display_name') or profile.get('username') or 'Player'

        player_won = (outcome == call)

        if player_won:
            winnings_int = int(bet_amount * CF_MULTIPLIER)
            paid = adjust_user_balance(user_id, winnings_int, game=True)
            if paid is False:
                result_line = "🔧 <b>Casino Maintenance</b>\n\nUnable to process win right now. Please try again shortly."
            else:
                user_balances[user_id] = get_user_balance(user_id)
                stats_game_type = 'coinflip'
                update_game_stats(user_id, stats_game_type, bet_amount, winnings_int, True)
                result_line = f"🎉 <b>{display_name}</b> wins and earns <b>${payout_usd:.2f}</b> ({CF_MULTIPLIER}x)"
        else:
            update_game_stats(user_id, 'coinflip', bet_amount, 0, False)
            result_line = f"🤖 <b>Bot</b> wins and earns <b>${payout_usd:.2f}</b> ({CF_MULTIPLIER}x)"

        del coinflip_sessions[user_id]

        # Store last bet for play again
        context.user_data['cf_last_bet'] = bet_amount

        game_over_keyboard = [
            [InlineKeyboardButton(t("btn_play_again", user_id=user_id), callback_data="cf_play_again")],
            [InlineKeyboardButton(t("back_to_games", user_id=user_id), callback_data="show_games")],
        ]
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"🏆 <b>Game Over!</b>\n\n"
                 f"<b>Outcome:</b> {outcome_display}\n\n"
                 f"{result_line}",
            reply_markup=InlineKeyboardMarkup(game_over_keyboard),
            parse_mode=ParseMode.HTML
        )
        return

    if data == "cf_cancel":
        # Refund if bet was already deducted
        if user_id in coinflip_sessions:
            session = coinflip_sessions[user_id]
            adjust_user_balance(user_id, session['bet'])
            user_balances[user_id] = get_user_balance(user_id)
            del coinflip_sessions[user_id]

        context.user_data.pop('cf_bet', None)
        context.user_data.pop('cf_call', None)

        await query.edit_message_text(t("cf_cancelled", user_id=user_id), parse_mode=ParseMode.HTML)
        return

    if data == "cf_play_again":
        last_bet = context.user_data.get('cf_last_bet', 0)
        if last_bet <= 0:
            await query.answer()
            await query.edit_message_text(
                "🎲 <b>Coinflip</b>\n\nUse /cf <amount> to play!",
                parse_mode=ParseMode.HTML
            )
            return

        if user_id in coinflip_sessions:
            await query.answer(t("err_active_coinflip", user_id=user_id), show_alert=True)
            return

        balance = get_user_balance(user_id)
        if balance < last_bet:
            await query.answer(f"❌ Insufficient balance! You have {balance} ⭐", show_alert=True)
            return

        await query.answer()
        context.user_data['cf_bet'] = last_bet

        keyboard = [
            [
                InlineKeyboardButton(t("cf_heads", user_id=user_id), callback_data="cf_heads"),
                InlineKeyboardButton(t("cf_tails", user_id=user_id), callback_data="cf_tails"),
            ],
            [InlineKeyboardButton(t("btn_cancel", user_id=user_id), callback_data="cf_cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            f"🎲 <b>Coinflip — {last_bet} ⭐</b>\n\n"
            f"Call the side you believe the coin will land on:",
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
        return

    # Copy emoji button fallback (for older telegram lib without CopyTextButton)
