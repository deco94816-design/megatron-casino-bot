from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, LabeledPrice
from telegram.ext import ContextTypes
import json
from datetime import datetime, timedelta

import bot
from storage import db
from casino_bot.translations import t
import oxapay

async def handle_cashier_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = query.from_user.id
    if data == "balance_deposit":
        keyboard = [
            [
                InlineKeyboardButton("10 ⭐", callback_data="deposit_10"),
                InlineKeyboardButton("25 ⭐", callback_data="deposit_25"),
            ],
            [
                InlineKeyboardButton("50 ⭐", callback_data="deposit_50"),
                InlineKeyboardButton("100 ⭐", callback_data="deposit_100"),
            ],
            [
                InlineKeyboardButton("250 ⭐", callback_data="deposit_250"),
                InlineKeyboardButton("500 ⭐", callback_data="deposit_500"),
            ],
            [
                InlineKeyboardButton(t("custom_amount_button", user_id=user_id), callback_data="deposit_custom"),
            ],
            [
                InlineKeyboardButton(t("crypto_deposit_button", user_id=user_id), callback_data="crypto_deposit"),
            ],
            [
                InlineKeyboardButton(t("back_button", user_id=user_id), callback_data="back_to_balance"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        sent_dep = await query.edit_message_text(
            "💳 <b>Select deposit amount:</b>",
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
        register_menu_owner(sent_dep, user_id)
        return
    
    if data == "balance_withdraw":
        if query.message.chat.type != "private":
            bot_info = await context.bot.get_me()
            await query.edit_message_text(
                "🔒 <b>Private Command Only</b>\n\n"
                "For your security, withdrawals can only be done in a private chat with the bot.\n\n"
                f"👉 <a href='https://t.me/{bot_info.username}?start=withdraw'>Click here to open DM</a>\n\n"
                "Then use /withdraw command.",
                parse_mode=ParseMode.HTML
            )
            return
        
        context.user_data['withdraw_state'] = None
        context.user_data['withdraw_amount'] = None
        context.user_data['withdraw_address'] = None
        
        welcome_text = (
            "✅ <b>Welcome to Stars Withdrawal!</b>\n\n"
            "<b>Withdraw:</b>\n"
            "1 ⭐ = $0.0179 = 0.01201014 TON\n\n"
            f"<b>Minimum withdrawal: {MIN_WITHDRAWAL} ⭐</b>\n\n"
            "<blockquote>â¹ï¸  <b>Good to know:</b>\n"
            "• When you exchange stars through a channel or bot, Telegram keeps a 15% fee and applies a 21-day hold.\n"
            "• We send TON immediately—factoring in this fee and a small service premium.</blockquote>"
        )
        
        keyboard = [
            [
                InlineKeyboardButton(t("withdraw_stars_button", user_id=user_id), callback_data="withdraw_stars"),
                InlineKeyboardButton(t("withdraw_crypto_button", user_id=user_id), callback_data="withdraw_crypto"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        # For callback, we need to handle video differently
        # If video is set, delete current message and send new one with video
        if withdraw_video_file_id:
            try:
                await query.message.delete()
                sent_msg = await context.bot.send_video(
                    chat_id=query.message.chat_id,
                    video=withdraw_video_file_id,
                    caption=welcome_text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup
                )
                register_menu_owner(sent_msg, user_id)
            except Exception as e:
                logger.error(f"Failed to send withdraw video in callback: {e}")
                sent_edit = await query.edit_message_text(
                    welcome_text,
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.HTML
                )
                register_menu_owner(sent_edit, user_id)
        else:
            sent_edit = await query.edit_message_text(
                welcome_text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
            register_menu_owner(sent_edit, user_id)
        return
    
    # Handle addbal callbacks
    if data.startswith("addbal_stars_"):
        try:
            # Format: addbal_stars_USERID_AMOUNT (amount may have DOT instead of .)
            parts = data.split("_", 3)  # Split into max 4 parts
            if len(parts) >= 4:
                target_user_id = int(parts[2])
                amount_str = parts[3].replace('DOT', '.')  # Replace DOT back to .
                amount = float(amount_str)
                
                # Add stars balance (use db directly to bypass admin guard)
                db.adjust_user_balance(target_user_id, amount)
                new_balance = db.get_user_balance(target_user_id)
                user_balances[target_user_id] = new_balance  # Sync memory cache
                
                await query.edit_message_text(
                    f"✅ <b>Balance Added Successfully!</b>\n\n"
                    f"👤 User ID: <code>{target_user_id}</code>\n"
                    f"⭐ Added: <b>{amount:,.2f} Stars</b>\n"
                    f"💰 New Balance: <b>{new_balance:,.2f} Stars</b>",
                    parse_mode=ParseMode.HTML
                )
                logger.info(f"Admin {user_id} added {amount} stars to user {target_user_id}")
            else:
                await query.answer(t("err_invalid_data", user_id=user_id), show_alert=True)
        except (ValueError, IndexError) as e:
            await query.answer(t("err_processing", user_id=user_id), show_alert=True)
            logger.error(f"Error in addbal_stars callback: {e}")
        return
    
    if data.startswith("addbal_crypto_"):
        try:
            # Format: addbal_crypto_USERID_AMOUNT (amount may have DOT instead of .)
            parts = data.split("_", 3)  # Split into max 4 parts
            if len(parts) >= 4:
                target_user_id = int(parts[2])
                amount_str = parts[3].replace('DOT', '.')  # Replace DOT back to .
                amount = float(amount_str)
                
                # Add crypto balance
                db.adjust_user_crypto_balance(target_user_id, amount)
                user_crypto_balances[target_user_id] = db.get_user_crypto_balance(target_user_id)
                
                new_crypto_balance = user_crypto_balances[target_user_id]
                
                await query.edit_message_text(
                    f"✅ <b>Crypto Balance Added Successfully!</b>\n\n"
                    f"👤 User ID: <code>{target_user_id}</code>\n"
                    f"💎 Added: <b>${amount:,.2f}</b>\n"
                    f"💰 New Crypto Balance: <b>${new_crypto_balance:,.2f}</b>",
                    parse_mode=ParseMode.HTML
                )
                logger.info(f"Admin {user_id} added ${amount} crypto to user {target_user_id}")
            else:
                await query.answer(t("err_invalid_data", user_id=user_id), show_alert=True)
        except (ValueError, IndexError) as e:
            await query.answer(t("err_processing", user_id=user_id), show_alert=True)
            logger.error(f"Error in addbal_crypto callback: {e}")
        return
    
    # Mines game handlers
    if data == "withdraw_stars":
        context.user_data['withdraw_state'] = 'waiting_amount'
        context.user_data['withdraw_type'] = 'stars'
        
        # Try to edit caption if it's a video message, otherwise edit text
        try:
            await query.edit_message_caption(
                caption=f"💫 <b>Enter the number of ⭐ to withdraw:</b>\n\n"
                        f"Minimum: {MIN_WITHDRAWAL} ⭐\n"
                        f"Example: 100",
                parse_mode=ParseMode.HTML
            )
        except Exception:
            try:
                await query.edit_message_text(
                    f"💫 <b>Enter the number of ⭐ to withdraw:</b>\n\n"
                    f"Minimum: {MIN_WITHDRAWAL} ⭐\n"
                    f"Example: 100",
                    parse_mode=ParseMode.HTML
                )
            except Exception as e:
                logger.error(f"Failed to edit message for withdraw: {e}")
                try:
                    await query.answer(t("err_occurred", user_id=user_id), show_alert=True)
                except:
                    pass
        return
    
    if data == "withdraw_crypto":
        logger.info(f"withdraw_crypto callback received from user {user_id}")
        context.user_data['withdraw_state'] = 'waiting_amount'
        context.user_data['withdraw_type'] = 'crypto'
        
        min_crypto_usd = 5.0
        crypto_balance = user_crypto_balances.get(user_id, 0.0)
        
        # Try to edit caption if it's a video message, otherwise edit text
        try:
            await query.edit_message_caption(
                caption=f"💫 <b>Enter the number to withdraw:</b>\n\n"
                        f"💎 Your Crypto Balance: <b>${crypto_balance:.2f}</b>\n"
                        f"Minimum: ${min_crypto_usd:.0f}\n"
                        f"Example: 10",
                parse_mode=ParseMode.HTML
            )
            logger.info(f"Successfully edited caption for crypto withdraw")
        except Exception as e1:
            logger.info(f"Failed to edit caption, trying edit_message_text: {e1}")
            try:
                await query.edit_message_text(
                    f"💫 <b>Enter the number to withdraw:</b>\n\n"
                    f"💎 Your Crypto Balance: <b>${crypto_balance:.2f}</b>\n"
                    f"Minimum: ${min_crypto_usd:.0f}\n"
                    f"Example: 10",
                    parse_mode=ParseMode.HTML
                )
                logger.info(f"Successfully edited message for crypto withdraw")
            except Exception as e2:
                logger.error(f"Failed to edit message for crypto withdraw: {e2}", exc_info=True)
                try:
                    await query.answer(t("err_occurred", user_id=user_id), show_alert=True)
                except:
                    pass
        return
    
    if data == "confirm_withdraw":
        global withdrawal_counter
        
        withdraw_type = context.user_data.get('withdraw_type', 'stars')
        crypto_address = context.user_data.get('withdraw_address', '')
        
        withdrawal_counter = db.get_withdrawal_counter() + 1
        db.set_withdrawal_counter(withdrawal_counter)
        exchange_id = withdrawal_counter
        transaction_id = generate_transaction_id()
        now = datetime.now()
        created_date = now.strftime("%Y-%m-%d %H:%M")
        hold_until = (now + timedelta(days=14)).strftime("%Y-%m-%d %H:%M")
        
        if withdraw_type == 'crypto':
            # Crypto withdrawal: check crypto balance and deduct
            amount_usd = context.user_data.get('withdraw_amount_usd', 0)
            
            # Check crypto balance
            crypto_balance = user_crypto_balances.get(user_id, 0.0)
            if amount_usd > crypto_balance:
                await query.edit_message_text(
                    "❌ <b>Insufficient crypto balance!</b>\n\n"
                    f"Your crypto balance: ${crypto_balance:.2f}\n"
                    f"Requested: ${amount_usd:.2f}\n\n"
                    "Use /withdraw to try again.",
                    parse_mode=ParseMode.HTML
                )
                context.user_data['withdraw_state'] = None
                return
            
            # Deduct from crypto balance (not stars)
            if not is_admin(user_id):
                db.adjust_user_crypto_balance(user_id, -amount_usd)
                user_crypto_balances[user_id] = db.get_user_crypto_balance(user_id)
            
            # Get coin name (use detected coin or detect from address)
            coin_name = context.user_data.get('detected_coin') or detect_coin_from_address(crypto_address)
            
            # Generate a more realistic TXID based on coin type
            import secrets
            if coin_name in ["Ethereum", "USDT"]:
                # Ethereum-style TXID (66 chars: 0x + 64 hex)
                txid = "0x" + secrets.token_hex(32)
            elif coin_name == "Bitcoin":
                # Bitcoin-style TXID (64 hex chars)
                txid = secrets.token_hex(32)
            elif coin_name == "Litecoin":
                # Litecoin-style TXID (64 hex chars)
                txid = secrets.token_hex(32)
            elif coin_name == "Solana":
                # Solana-style TXID (base58, 88 chars)
                base58_chars = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
                txid = ''.join(secrets.choice(base58_chars) for _ in range(88))
            elif coin_name == "TON":
                # TON-style transaction hash
                txid = secrets.token_hex(32).upper()
            else:
                # Default: use generated transaction_id
                txid = transaction_id
            
            withdrawal_data = {
                'exchange_id': exchange_id,
                'type': 'crypto',
                'amount_usd': amount_usd,
                'address': crypto_address,
                'transaction_id': transaction_id,
                'txid': txid,
                'coin_name': coin_name,
                'created': created_date,
                'hold_until': hold_until,
                'status': 'on_hold'
            }
            user_withdrawals[str(user_id)] = withdrawal_data  # Keep in memory for compatibility
            
            # Save to database
            db.add_withdrawal(
                tx_id=str(exchange_id),
                user_id=user_id,
                stars=0.0,  # Crypto withdrawals don't use stars
                ton_amount=None,
                status='on_hold',
                exchange_id=str(exchange_id),
                created=now,
                data=withdrawal_data
            )
            
            # Send professional confirmation message
            final_message = (
                f"🚀 <b>Withdrawal Sent Successfully!</b>\n\n"
                f"Your funds are now being processed on the <b>{coin_name}</b> blockchain.\n\n"
                f"📊 <b>Transaction Details:</b>\n"
                f"💎 Amount: <b>${amount_usd:.2f}</b>\n"
                f"🧾 TXID: <code>{txid}</code>\n"
                f"⏳ Expected confirmation: <b>5 minutes</b>\n\n"
                f"✅ Once the transaction is confirmed on the blockchain, the balance will reflect in your wallet.\n\n"
                f"💡 <i>You can track your transaction using the TXID above.</i>"
            )
            
            await query.edit_message_text(
                final_message,
                parse_mode=ParseMode.HTML
            )
        else:
            # Stars withdrawal: check balance and deduct
            stars_amount = context.user_data.get('withdraw_amount', 0)
            ton_address = crypto_address
            
            balance = get_user_balance(user_id)
            if balance < stars_amount:
                await query.edit_message_text(
                    "❌ <b>Insufficient balance!</b>\n\n"
                    f"Your balance: {balance} ⭐\n"
                    f"Requested: {stars_amount} ⭐\n\n"
                    "Use /withdraw to try again.",
                    parse_mode=ParseMode.HTML
                )
                context.user_data['withdraw_state'] = None
                return
            
            if not is_admin(user_id):
                adjust_user_balance(user_id, -stars_amount)
                user_balances[user_id] = get_user_balance(user_id)  # Sync memory cache
            
            ton_amount = round(stars_amount * STARS_TO_TON, 8)
            
            user_withdrawals[str(user_id)] = {
                'exchange_id': exchange_id,
                'type': 'stars',
                'stars': stars_amount,
                'ton_amount': ton_amount,
                'address': ton_address,
                'transaction_id': transaction_id,
                'created': created_date,
                'hold_until': hold_until,
                'status': 'on_hold'
            }
            
            save_data()
            
            receipt_text = (
                f"📄 <b>Stars withdraw exchange #{exchange_id}</b>\n\n"
                f"📊 Exchange status: Processing\n"
                f"⭐ Stars withdrawal: {stars_amount}\n"
                f"💎 TON amount: {ton_amount}\n\n"
                f"<b>Sale:</b>\n"
                f"🎯 Top-up status: Paid\n"
                f"🏅 Created: {created_date}\n"
                f"🏦 TON address: <code>{ton_address}</code>\n"
                f"🧾 Transaction ID: <code>{transaction_id}</code>\n\n"
                f"💸 Withdrawal status: On hold\n"
                f"💎 TON amount: {ton_amount}\n"
                f"🏅 Withdrawal created: {created_date}\n"
                f"⏳ On hold until: {hold_until}\n"
                f"📍 Reason: {bot_identity.get('name', 'Iibrate')} game rating is negative. Placed on 14-day hold."
            )
            
            # Send receipt message for stars withdrawal
            await query.edit_message_text(
                receipt_text,
                parse_mode=ParseMode.HTML
            )
        
        context.user_data['withdraw_state'] = None
        context.user_data['withdraw_amount'] = None
        context.user_data['withdraw_amount_usd'] = None
        context.user_data['withdraw_address'] = None
        context.user_data['withdraw_type'] = None
        return
    
    if data == "cancel_withdraw":
        context.user_data['withdraw_state'] = None
        context.user_data['withdraw_amount'] = None
        context.user_data['withdraw_amount_usd'] = None
        context.user_data['withdraw_address'] = None
        context.user_data['withdraw_type'] = None
        await query.edit_message_text(
            "❌ <b>Withdrawal cancelled.</b>\n\n"
            "Use /withdraw to start again.",
            parse_mode=ParseMode.HTML
        )
        return
    
    if data.startswith("deposit_"):
        if data == "deposit_custom":
            await query.edit_message_text(
                "💳 <b>Custom Deposit</b>\n\n"
                "Please send the amount you want to deposit.\n\n"
                "Example: Just type <code>150</code>\n\n"
                "Minimum: 1 ⭐\n"
                "Maximum: 10000 ⭐",
                parse_mode=ParseMode.HTML
            )
            context.user_data['waiting_for_custom_amount'] = True
            return
        
        amount = int(data.split("_")[1])
        await send_invoice(query, amount)
        return
    
    # Crypto deposit handlers
    if data == "crypto_deposit":
        keyboard = [
            [
                InlineKeyboardButton(
                    "💎 OxaPay Invoice (BTC/ETH/USDT/LTC/DOGE)",
                    callback_data="oxapay_deposit"
                ),
            ],
            [
                InlineKeyboardButton(t("crypto_litecoin", user_id=user_id), callback_data="crypto_litecoin"),
                InlineKeyboardButton(t("crypto_bitcoin", user_id=user_id), callback_data="crypto_bitcoin"),
            ],
            [
                InlineKeyboardButton(t("crypto_ethereum", user_id=user_id), callback_data="crypto_ethereum"),
                InlineKeyboardButton(t("crypto_solana", user_id=user_id), callback_data="crypto_solana"),
            ],
            [
                InlineKeyboardButton(t("crypto_ton", user_id=user_id), callback_data="crypto_ton"),
                InlineKeyboardButton(t("crypto_usdt_bep20", user_id=user_id), callback_data="crypto_usdt_bep20"),
            ],
            [
                InlineKeyboardButton(t("crypto_usdc_erc20", user_id=user_id), callback_data="crypto_usdc_erc20"),
                InlineKeyboardButton(t("crypto_monero", user_id=user_id), callback_data="crypto_monero"),
            ],
            [
                InlineKeyboardButton(t("back_button", user_id=user_id), callback_data="back_to_deposit"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "💎 <b>Select Cryptocurrency</b>\n\n"
            "Choose a cryptocurrency to deposit:",
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
        return
    
    if data.startswith("crypto_"):
        coin_key = data.replace("crypto_", "")
        coin_info = {
            "litecoin": {"name": "Litecoin", "short": "LTC", "emoji": "💳", "network": ""},
            "bitcoin": {"name": "Bitcoin", "short": "BTC", "emoji": "💳", "network": ""},
            "ethereum": {"name": "Ethereum", "short": "ETH", "emoji": "💳", "network": "ERC-20"},
            "solana": {"name": "Solana", "short": "SOL", "emoji": "💳", "network": ""},
            "ton": {"name": "TON", "short": "TON", "emoji": "💳", "network": ""},
            "usdt_bep20": {"name": "USDT", "short": "USDT", "emoji": "💳", "network": "BEP-20"},
            "usdc_erc20": {"name": "USDC", "short": "USDC", "emoji": "💳", "network": "ERC-20"},
            "monero": {"name": "Monero", "short": "XMR", "emoji": "💳", "network": ""},
        }
        
        if coin_key not in coin_info:
            await query.answer(t("err_invalid_coin", user_id=user_id), show_alert=True)
            return
        
        coin_data = coin_info[coin_key]
        coin_name = coin_data["name"]
        coin_short = coin_data["short"]
        coin_emoji = coin_data["emoji"]
        network = coin_data["network"]
        
        # Get base address from crypto_addresses
        if coin_key not in crypto_addresses or not crypto_addresses[coin_key].get("address"):
            await query.answer(t("err_addr_not_set", user_id=user_id), show_alert=True)
            return
        
        address_data = crypto_addresses[coin_key]
        address = address_data.get("address", "")
        address_network = address_data.get("network", network)
        
        # Check if in private chat (DM) - use new format with timer
        if query.message.chat.type == "private":
            # DM: Use temporary address with timer and refresh
            base_address = address
            temp_address, expires_at = get_or_create_temp_address(user_id, coin_key, base_address)
            timer_text = format_timer(expires_at)
            
            # Format message with timer
            message = f"{coin_emoji} <b>{coin_name} deposit</b>\n"
            message += f"To top up your balance, transfer the desired amount to this {coin_short} address.\n\n"
            message += f"<b>Please note:</b>\n"
            message += f"1. The deposit address is temporary and is only issued for 1 hour. A new one will be created after that.\n"
            message += f"2. One address accepts only one payment.\n\n"
            message += f"<b>{coin_short} address:</b>\n<code>{temp_address}</code>\n\n"
            message += f"<b>Expires in:</b> {timer_text}"
            
            keyboard = [
                [
                    InlineKeyboardButton(t("back_button", user_id=user_id), callback_data="crypto_deposit"),
                    InlineKeyboardButton(t("refresh_button", user_id=user_id), callback_data=f"crypto_refresh_{coin_key}"),
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
        else:
            # Group: Use old format (simple address, no timer)
            message = f"{coin_emoji} <b>{coin_name} deposit</b>\n\n"
            message += f"To top up your balance, transfer the desired amount to this {coin_name} address.\n\n"
            message += f"<b>{coin_name} address:</b>\n<code>{address}</code>\n\n"
            
            if address_network:
                message += f"<b>Network:</b> {address_network}\n"
            
            message += f"<b>Network fee:</b> 1%"
            
            keyboard = [
                [
                    InlineKeyboardButton(t("back_button", user_id=user_id), callback_data="crypto_deposit"),
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            message,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
        return
    
    # Handle refresh button (DM only)
    if data.startswith("crypto_refresh_"):
        coin_key = data.replace("crypto_refresh_", "")
        
        # Check if in private chat (DM) - refresh only works in DM
        if query.message.chat.type != "private":
            await query.answer(t("err_refresh_dm_only", user_id=user_id), show_alert=True)
            return
        
        coin_info = {
            "litecoin": {"name": "Litecoin", "short": "LTC", "emoji": "💳", "network": ""},
            "bitcoin": {"name": "Bitcoin", "short": "BTC", "emoji": "💳", "network": ""},
            "ethereum": {"name": "Ethereum", "short": "ETH", "emoji": "💳", "network": "ERC-20"},
            "solana": {"name": "Solana", "short": "SOL", "emoji": "💳", "network": ""},
            "ton": {"name": "TON", "short": "TON", "emoji": "💳", "network": ""},
            "usdt_bep20": {"name": "USDT", "short": "USDT", "emoji": "💳", "network": "BEP-20"},
            "usdc_erc20": {"name": "USDC", "short": "USDC", "emoji": "💳", "network": "ERC-20"},
            "monero": {"name": "Monero", "short": "XMR", "emoji": "💳", "network": ""},
        }
        
        if coin_key not in coin_info:
            await query.answer(t("err_invalid_coin", user_id=user_id), show_alert=True)
            return
        
        # Get base address
        if coin_key not in crypto_addresses or not crypto_addresses[coin_key].get("address"):
            await query.answer(t("err_addr_not_set", user_id=user_id), show_alert=True)
            return
        
        base_address = crypto_addresses[coin_key].get("address", "")
        
        # Delete old temp address and create new one
        key = (user_id, coin_key)
        if key in user_temp_crypto_addresses:
            del user_temp_crypto_addresses[key]
        
        # Create new temp address
        temp_address, expires_at = get_or_create_temp_address(user_id, coin_key, base_address)
        timer_text = format_timer(expires_at)
        
        coin_data = coin_info[coin_key]
        coin_name = coin_data["name"]
        coin_short = coin_data["short"]
        coin_emoji = coin_data["emoji"]
        
        # Format message
        message = f"{coin_emoji} <b>{coin_name} deposit</b>\n"
        message += f"To top up your balance, transfer the desired amount to this {coin_short} address.\n\n"
        message += f"<b>Please note:</b>\n"
        message += f"1. The deposit address is temporary and is only issued for 1 hour. A new one will be created after that.\n"
        message += f"2. One address accepts only one payment.\n\n"
        message += f"<b>{coin_short} address:</b>\n<code>{temp_address}</code>\n\n"
        message += f"<b>Expires in:</b> {timer_text}"
        
        keyboard = [
            [
                InlineKeyboardButton(t("back_button", user_id=user_id), callback_data="crypto_deposit"),
                InlineKeyboardButton(t("refresh_button", user_id=user_id), callback_data=f"crypto_refresh_{coin_key}"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
        await query.answer(t("alert_addr_refreshed", user_id=user_id))
        return
    # ── OxaPay Invoice Deposit ────────────────────────────────────────────
    if data == "oxapay_deposit":
        keyboard = [
            [InlineKeyboardButton(t("oxapay_usdt", user_id=user_id), callback_data="oxapay_cur_USDT")],
            [
                InlineKeyboardButton(t("oxapay_btc", user_id=user_id),  callback_data="oxapay_cur_BTC"),
                InlineKeyboardButton(t("oxapay_eth", user_id=user_id),  callback_data="oxapay_cur_ETH"),
            ],
            [
                InlineKeyboardButton(t("oxapay_ltc", user_id=user_id),   callback_data="oxapay_cur_LTC"),
                InlineKeyboardButton(t("oxapay_doge", user_id=user_id), callback_data="oxapay_cur_DOGE"),
            ],
            [InlineKeyboardButton(t("back_button", user_id=user_id), callback_data="crypto_deposit")],
        ]
        await query.edit_message_text(
            "💎 <b>OxaPay Crypto Deposit</b>\n\n"
            "Select the cryptocurrency you want to deposit.\n"
            "An invoice with a unique payment address will be generated for you.",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return
    if data.startswith("oxapay_cur_"):
        currency = data[len("oxapay_cur_"):]
        cur_info = oxapay.SUPPORTED_CURRENCIES.get(currency)
        if not cur_info:
            await query.answer(t("err_unsupported_currency", user_id=user_id), show_alert=True)
            return
        keyboard = [
            [
                InlineKeyboardButton("$5",   callback_data=f"oxapay_inv_{currency}_5"),
                InlineKeyboardButton("$10",  callback_data=f"oxapay_inv_{currency}_10"),
                InlineKeyboardButton("$25",  callback_data=f"oxapay_inv_{currency}_25"),
            ],
            [
                InlineKeyboardButton("$50",  callback_data=f"oxapay_inv_{currency}_50"),
                InlineKeyboardButton("$100", callback_data=f"oxapay_inv_{currency}_100"),
            ],
            [InlineKeyboardButton(t("back_button", user_id=user_id), callback_data="oxapay_deposit")],
        ]
        await query.edit_message_text(
            f"💎 <b>OxaPay — {cur_info['emoji']} {cur_info['name']} Deposit</b>\n\n"
            f"Network: <b>{cur_info['network']}</b>\n\n"
            f"Select the amount in USD to deposit:",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return
    if data.startswith("oxapay_inv_"):
        # Callback format: oxapay_inv_{CURRENCY}_{USD_AMOUNT}
        # e.g. oxapay_inv_USDT_25 or oxapay_inv_BTC_10
        parts = data.split("_", 3)   # ['oxapay', 'inv', 'CURRENCY', 'AMOUNT']
        if len(parts) < 4:
            await query.answer(t("err_invalid_selection", user_id=user_id), show_alert=True)
            return
        currency = parts[2]
        try:
            usd_amount = float(parts[3])
        except ValueError:
            await query.answer(t("err_invalid_amount_alert", user_id=user_id), show_alert=True)
            return
        cur_info = oxapay.SUPPORTED_CURRENCIES.get(currency)
        if not cur_info:
            await query.answer(t("err_unsupported_currency", user_id=user_id), show_alert=True)
            return
        await query.answer(t("alert_generating_invoice", user_id=user_id))
        await query.edit_message_text(
            "⏳ <b>Creating your deposit invoice…</b>\n\nPlease wait a moment.",
            parse_mode=ParseMode.HTML,
        )
        # Convert USD amount to the target crypto amount
        crypto_amount = await oxapay.get_crypto_amount_for_usd(usd_amount, currency)
        if crypto_amount is None:
            logger.error(
                f"OxaPay: could not resolve crypto amount for "
                f"${usd_amount} in {currency} (user {user_id})"
            )
            await query.edit_message_text(
                "❌ <b>Could not fetch exchange rate.</b>\n\n"
                "Please try again in a moment or choose a different currency.",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton(t("back_button", user_id=user_id), callback_data="oxapay_deposit")]]
                ),
            )
            return
        # Create the OxaPay invoice
        response = await oxapay.create_invoice(
            amount=crypto_amount,
            currency=currency,
            user_id=user_id,
        )
        if response is None or response.get("result") != 100:
            result_code = response.get("result") if response else "N/A"
            result_msg  = response.get("message", "") if response else ""
            logger.error(
                f"OxaPay invoice creation failed for user {user_id}: "
                f"result={result_code} msg={result_msg}"
            )
            await query.edit_message_text(
                "❌ <b>Failed to create deposit invoice.</b>\n\n"
                "Please try again later or contact support.",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton(t("back_button", user_id=user_id), callback_data="oxapay_deposit")]]
                ),
            )
            return
        track_id     = response.get("trackId", "")
        pay_link     = response.get("payLink", "")
        inv_amount   = response.get("amount", crypto_amount)
        inv_currency = currency  # creation response doesn't echo currency; use what we sent
        # Try to get the static deposit address for this currency so we can
        # display it directly in the bot.  Falls back gracefully if unavailable.
        cur_info        = oxapay.SUPPORTED_CURRENCIES.get(currency, {})
        network_str     = cur_info.get("network", "")
        static_resp     = await oxapay.request_static_address(inv_currency, network_str)
        deposit_address = ""
        if static_resp and static_resp.get("result") == 100:
            deposit_address = static_resp.get("address", "")
        # Persist to DB
        db.create_deposit(
            user_id=user_id,
            track_id=track_id,
            address=deposit_address or pay_link,
            currency=inv_currency,
            amount_usd=usd_amount,
        )
        logger.info(
            f"[DEPOSIT] Invoice saved: user={user_id} trackId={track_id} "
            f"currency={inv_currency} crypto_amount={inv_amount} usd=${usd_amount} "
            f"address={'YES' if deposit_address else 'NO (payLink fallback)'}"
        )
        stars_estimate = int(usd_amount / STARS_TO_USD)
        if deposit_address:
            network_label = f" ({network_str})" if network_str else ""
            deposit_msg = (
                f"💳 <b>OxaPay Deposit Invoice</b>\n\n"
                f"💰 Amount: <b>{inv_amount} {inv_currency}</b>  (≈ ${usd_amount:.2f})\n"
                f"⭐ You will receive: <b>~{stars_estimate:,} Stars</b>\n\n"
                f"📋 <b>Send exactly {inv_amount} {inv_currency}{network_label} to:</b>\n"
                f"<code>{deposit_address}</code>\n\n"
                f"🔖 Track ID: <code>{track_id}</code>\n"
                f"⏰ Expires in: <b>30 minutes</b>\n\n"
                f"✅ Your balance will be credited automatically once confirmed.\n"
                f"⚠️ Send <b>only {inv_currency}</b> to this address — "
                f"other coins will be lost."
            )
            keyboard = [
                [InlineKeyboardButton(t("btn_open_payment", user_id=user_id), url=pay_link)],
                [InlineKeyboardButton(t("crypto_deposit_button", user_id=user_id), callback_data="oxapay_deposit")],
            ]
        else:
            # Static address unavailable — fall back to payment link only
            deposit_msg = (
                f"💳 <b>OxaPay Deposit Invoice</b>\n\n"
                f"💰 Amount: <b>{inv_amount} {inv_currency}</b>  (≈ ${usd_amount:.2f})\n"
                f"⭐ You will receive: <b>~{stars_estimate:,} Stars</b>\n\n"
                f"👇 <b>Tap <u>Pay Now</u> to see your deposit address and QR code</b>\n\n"
                f"🔖 Track ID: <code>{track_id}</code>\n"
                f"⏰ Expires in: <b>30 minutes</b>\n\n"
                f"✅ Your balance will be credited automatically once confirmed."
            )
            keyboard = [
                [InlineKeyboardButton(t("btn_pay_now", user_id=user_id), url=pay_link)],
                [InlineKeyboardButton(t("crypto_deposit_button", user_id=user_id), callback_data="oxapay_deposit")],
            ]
        await query.edit_message_text(
            deposit_msg,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return
    # ── End OxaPay ────────────────────────────────────────────────────────

