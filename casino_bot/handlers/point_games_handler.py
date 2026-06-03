from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ContextTypes
import json
import random
import asyncio
from datetime import datetime

import bot
from storage import db
from casino_bot.translations import t
from casino_bot.config import STARS_TO_USD, GAME_CONFIG, GAME_TYPES, MULTIPLIERS

async def handle_point_games_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = query.from_user.id
    if data.startswith("play_game_"):
        game_type = data.replace("play_game_", "")
        if game_type not in GAME_CONFIG:
            await query.answer(t("err_unknown_game", user_id=user_id), show_alert=True)
            return
        
        if user_id in game_sessions:
            await query.edit_message_text(
                "❌ You already have an active game! Finish it first.",
                parse_mode=ParseMode.HTML
            )
            return
        
        balance = get_user_balance(user_id)
        if balance < 1 and not is_admin(user_id):
            await query.edit_message_text(
                "❌ Insufficient balance! Use /deposit to add Stars.\n"
                f"Your balance: <b>{balance} ⭐</b>",
                parse_mode=ParseMode.HTML
            )
            return
        
        config = GAME_CONFIG[game_type]
        context.user_data['game_type'] = game_type
        
        keyboard = [
            [
                InlineKeyboardButton("10 ⭐", callback_data=f"bet_{game_type}_10"),
                InlineKeyboardButton("25 ⭐", callback_data=f"bet_{game_type}_25"),
            ],
            [
                InlineKeyboardButton("50 ⭐", callback_data=f"bet_{game_type}_50"),
                InlineKeyboardButton("100 ⭐", callback_data=f"bet_{game_type}_100"),
            ],
            [
                InlineKeyboardButton(t("back_to_games", user_id=user_id), callback_data="show_games"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        sent_pg = await query.edit_message_text(
            f"{config['emoji']} <b>{config['name']}</b>\n\n"
            f"💰 Choose your bet:\n"
            f"Your balance: <b>{balance:,} ⭐</b>",
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
        register_menu_owner(sent_pg, user_id)
        return
    
    if data.startswith("demo_game_"):
        if not is_admin(user_id):
            await query.answer(t("err_admin_only_alert", user_id=user_id), show_alert=True)
            return
        
        game_type = data.replace("demo_game_", "")
        if game_type not in GAME_CONFIG:
            await query.answer(t("err_unknown_game", user_id=user_id), show_alert=True)
            return
        
        context.user_data['game_type'] = game_type
        context.user_data['is_demo'] = True
        context.user_data['bet_amount'] = 100  # Demo bet
        
        config = GAME_CONFIG[game_type]
        keyboard = [
            [InlineKeyboardButton(t("mode_normal", user_id=user_id), callback_data=f"mode_normal_{game_type}")],
            [InlineKeyboardButton(t("mode_double", user_id=user_id), callback_data=f"mode_double_{game_type}")],
            [InlineKeyboardButton(t("mode_crazy", user_id=user_id), callback_data=f"mode_crazy_{game_type}")],
            [InlineKeyboardButton(t("back_button", user_id=user_id), callback_data="back_to_demo_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"🎮 <b>DEMO: {config['name']}</b> 🔑\n\n"
            "🎲 <b>Select game mode</b>\n\n"
            "<i>• Normal mode: Highest value wins\n"
            "• Crazy mode: Lowest value wins\n"
            "• Double mode: 2 emojis are rolled in 1 round</i>\n\n"
            "(No Stars will be deducted)",
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
        return
    
    if data == "back_to_demo_menu":
        keyboard = [
            [
                InlineKeyboardButton(t("demo_dice_btn", user_id=user_id), callback_data="demo_game_dice"),
                InlineKeyboardButton(t("demo_bowl_btn", user_id=user_id), callback_data="demo_game_bowl"),
            ],
            [
                InlineKeyboardButton(t("demo_dart_btn", user_id=user_id), callback_data="demo_game_dart"),
                InlineKeyboardButton(t("demo_football_btn", user_id=user_id), callback_data="demo_game_football"),
            ],
            [
                InlineKeyboardButton(t("demo_basketball_btn", user_id=user_id), callback_data="demo_game_basket"),
            ],
            [
                InlineKeyboardButton(t("btn_cancel_demo", user_id=user_id), callback_data="cancel_demo"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"🎮 <b>DEMO MODE</b> 🔑\n\n"
            f"🎯 Choose a game to test:\n"
            f"(No Stars will be deducted)",
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
        return
    
    if data == "cancel_demo":
        await query.edit_message_text(
            translate_text("❌ Demo cancelled.", user_id=user_id),
            parse_mode=ParseMode.HTML
        )
        return
    
    # ===== NEW POINT-BASED GAME CALLBACKS =====
    
    # Bet selection callback
    if data.startswith("bet_"):
        parts = data.split("_")
        game_type = parts[1]
        bet_amount = int(parts[2])
        
        if game_type not in GAME_CONFIG:
            await query.answer(t("err_unknown_game", user_id=user_id), show_alert=True)
            return
        
        balance = get_user_balance(user_id)
        
        if balance < bet_amount and not is_admin(user_id):
            await query.edit_message_text(
                "❌ Insufficient balance! Use /deposit to add Stars.",
                parse_mode=ParseMode.HTML
            )
            return
        
        context.user_data['bet_amount'] = bet_amount
        context.user_data['game_type'] = game_type
        
        config = GAME_CONFIG[game_type]
        keyboard = [
            [InlineKeyboardButton(t("mode_normal", user_id=user_id), callback_data=f"mode_normal_{game_type}")],
            [InlineKeyboardButton(t("mode_double", user_id=user_id), callback_data=f"mode_double_{game_type}")],
            [InlineKeyboardButton(t("mode_crazy", user_id=user_id), callback_data=f"mode_crazy_{game_type}")],
            [InlineKeyboardButton(t("cancel_game", user_id=user_id), callback_data=f"cancel_{game_type}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        sent_bet = await query.edit_message_text(
            "🎲 <b>Select game mode</b>\n\n"
            "<i>• Normal mode: Highest value wins\n"
            "• Crazy mode: Lowest value wins\n"
            "• Double mode: 2 emojis are rolled in 1 round</i>",
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
        register_menu_owner(sent_bet, user_id)
        return
    
    # Mode selection callback
    if data.startswith("mode_"):
        parts = data.split("_")
        mode = parts[1]  # normal, double, crazy
        game_type = parts[2]
        
        if game_type not in GAME_CONFIG:
            await query.answer(t("err_unknown_game", user_id=user_id), show_alert=True)
            return
        
        context.user_data['mode'] = mode
        config = GAME_CONFIG[game_type]
        
        keyboard = [
            [InlineKeyboardButton(t("btn_up_to_1", user_id=user_id), callback_data=f"points_1_{game_type}")],
            [InlineKeyboardButton(t("btn_up_to_2", user_id=user_id), callback_data=f"points_2_{game_type}")],
            [InlineKeyboardButton(t("btn_up_to_3", user_id=user_id), callback_data=f"points_3_{game_type}")],
            [InlineKeyboardButton("↩ Back", callback_data=f"back_to_mode_{game_type}")],
            [InlineKeyboardButton("🗑 Delete", callback_data=f"cancel_{game_type}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        sent_mode = await query.edit_message_text(
            "🎲 <b>Select the number of points needed to win</b>\n\n"
            "<i>ℹ️ The first player to win the selected number of rounds wins</i>",
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
        register_menu_owner(sent_mode, user_id)
        return
    
    # Points selection callback
    if data.startswith("points_"):
        parts = data.split("_")
        points_target = int(parts[1])
        game_type = parts[2]
        
        if game_type not in GAME_CONFIG:
            await query.answer(t("err_unknown_game", user_id=user_id), show_alert=True)
            return
        
        bet_amount = context.user_data.get('bet_amount', 10)
        mode = context.user_data.get('mode', 'normal')
        is_demo = context.user_data.get('is_demo', False)
        config = GAME_CONFIG[game_type]
        multiplier = MULTIPLIERS[mode]
        bet_usd = bet_amount * STARS_TO_USD
        
        # Mode descriptions
        mode_display = mode.capitalize()
        if mode == "normal":
            desc = f"the one with the higher {config['action']} wins"
        elif mode == "double":
            desc = f"each player goes twice — highest total wins the round"
        elif mode == "crazy":
            desc = f"the one with the LOWER {config['action']} wins"
        else:
            desc = ""
        
        keyboard = [
            [
                InlineKeyboardButton(f"{config['emoji']} Play now! {config['emoji']}", callback_data=f"play_{game_type}"),
            ],
            [
                InlineKeyboardButton(t("btn_cancel_game", user_id=user_id), callback_data=f"cancel_{game_type}"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        context.user_data['points_target'] = points_target
        
        demo_tag = " 🔑 DEMO" if is_demo else ""
        
        sent_pts = await query.edit_message_text(
            f"{config['emoji']} <b>{config['name']} vs 🤖 Bot</b>{demo_tag}\n\n"
            f"💰 Bet: <b>{bet_amount} ⭐</b> (${bet_usd:.2f})\n"
            f"📈 Multiplier: <b>×{multiplier}</b>\n"
            f"🎮 Mode: {mode_display} - Up to {points_target} point{'s' if points_target > 1 else ''}\n\n"
            f"Take turns {config['action']}ing {config['emoji']} — {desc}",
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
        register_menu_owner(sent_pts, user_id)
        return
    
    # Replay with same settings from last game
    if data.startswith("replay_"):
        game_type = data.replace("replay_", "")
        if game_type not in GAME_CONFIG:
            await query.answer(t("err_unknown_game", user_id=user_id), show_alert=True)
            return
        if user_id in game_sessions:
            await query.answer(t("err_active_game", user_id=user_id), show_alert=True)
            return
        last = user_last_game_settings.get(user_id)
        if last and last.get('game_type') == game_type:
            bet_amount = last['bet_amount']
            mode = last.get('mode', 'normal')
            points_target = last.get('points_target', 1)
        else:
            bet_amount = 10
            mode = 'normal'
            points_target = 1
        balance = get_user_balance(user_id)
        if balance < bet_amount and not is_admin(user_id):
            await query.answer(f"❌ Insufficient balance! You have {balance} ⭐", show_alert=True)
            return
        await query.answer()
        # Deduct balance
        if not is_admin(user_id):
            adjust_user_balance(user_id, -bet_amount, game=True)
            user_balances[user_id] = get_user_balance(user_id)
        multiplier = MULTIPLIERS[mode]
        config = GAME_CONFIG[game_type]
        game_sessions[user_id] = {
            "game_type": game_type,
            "mode": mode,
            "points_target": points_target,
            "player_score": 0,
            "bot_score": 0,
            "bet": bet_amount,
            "multiplier": multiplier,
            "chat_id": query.message.chat_id,
            "message_id": query.message.message_id,
            "is_demo": False,
            "player_rolls_needed": 2 if mode == "double" else 1,
            "player_rolls_done": 0,
            "player_total": 0,
            "waiting_for_player": True,
        }
        profile = get_or_create_profile(user_id)
        display_name = profile.get('display_name') or profile.get('username') or 'Player'
        user_link = get_user_link(user_id, display_name)
        bet_usd = bet_amount * STARS_TO_USD
        payout_usd = bet_usd * multiplier
        await query.edit_message_text(
            f"{config['emoji']} <b>{display_name} wants to play {config['name']}!</b>\n\n"
            f"Bet: ${bet_usd:.2f}\n"
            f"Payout: ${payout_usd:.2f} {multiplier}x\n\n"
            f"👤 {user_link}, it's your turn.",
            parse_mode=ParseMode.HTML,
            reply_markup=build_copy_turn_reply_markup(user_id, config['emoji'])
        )
        return
    # Play button callback - starts the actual game
    if data.startswith("play_") and not data.startswith("play_game_"):
        game_type = data.replace("play_", "")
        
        if game_type not in GAME_CONFIG:
            await query.answer(t("err_unknown_game", user_id=user_id), show_alert=True)
            return
        
        if user_id in game_sessions:
            await query.answer(t("err_active_game", user_id=user_id), show_alert=True)
            return
        
        bet_amount = context.user_data.get('bet_amount', 10)
        mode = context.user_data.get('mode', 'normal')
        points_target = context.user_data.get('points_target', 1)
        is_demo = context.user_data.get('is_demo', False)
        multiplier = MULTIPLIERS[mode]
        config = GAME_CONFIG[game_type]
        
        # Deduct balance
        if not is_demo and not is_admin(user_id):
            balance = get_user_balance(user_id)
            if balance < bet_amount:
                await query.edit_message_text(
                    "❌ Insufficient balance! Use /deposit to add Stars.",
                    parse_mode=ParseMode.HTML
                )
                return
            adjust_user_balance(user_id, -bet_amount, game=True)
            new_balance = get_user_balance(user_id)
            expected_balance = balance - bet_amount
            if abs(new_balance - expected_balance) > 0.01:
                set_user_balance(user_id, expected_balance)
            user_balances[user_id] = get_user_balance(user_id)
        
        # Create session
        game_sessions[user_id] = {
            "game_type": game_type,
            "mode": mode,
            "points_target": points_target,
            "player_score": 0,
            "bot_score": 0,
            "bet": bet_amount,
            "multiplier": multiplier,
            "chat_id": query.message.chat_id,
            "message_id": query.message.message_id,
            "is_demo": is_demo,
            "player_rolls_needed": 2 if mode == "double" else 1,
            "player_rolls_done": 0,
            "player_total": 0,
            "waiting_for_player": True,
        }
        # Get display name for start message
        profile = get_or_create_profile(user_id)
        display_name = profile.get('display_name') or profile.get('username') or 'Player'
        user_link = get_user_link(user_id, display_name)
        bet_usd = bet_amount * STARS_TO_USD
        payout_usd = bet_usd * multiplier
        await query.edit_message_text(
            f"{config['emoji']} <b>{display_name} wants to play {config['name']}!</b>\n\n"
            f"Bet: ${bet_usd:.2f}\n"
            f"Payout: ${payout_usd:.2f} {multiplier}x\n\n"
            f"👤 {user_link}, it's your turn.",
            parse_mode=ParseMode.HTML,
            reply_markup=build_copy_turn_reply_markup(user_id, config['emoji'])
        )
        return
    
    # ---- ââââ COINFLIP CALLBACKS ââââ ----

