"""Balance service — user balance operations."""

# These functions are extracted for reference.
# The originals in the main file still handle actual DB calls.
# This module will be wired up in Phase 5.

def get_user_balance(user_id):
    if is_admin(user_id):
        return ADMIN_BALANCE
    return db.get_user_balance(user_id)


# ==================== TRANSLATION SYSTEM ====================



def set_user_balance(user_id, amount):
    if not is_admin(user_id):
        db.set_user_balance(user_id, amount)




def adjust_user_balance(user_id, amount, game=False):
    global active_jackpot_stars
    if not is_admin(user_id):
        if game:
            if amount > 0:
                # Win: check if bankroll can cover the payout
                payout_usd = round(amount * STARS_TO_USD, 2)
                if casino_bankroll_usd < payout_usd:
                    _bankroll_win_blocked.add(user_id)
                    logger.warning(f"[BANKROLL] Win BLOCKED user={user_id} payout=${payout_usd:.2f} bankroll=${casino_bankroll_usd:.2f}")
                    return False
                _bankroll_win_blocked.discard(user_id)
                adjust_bankroll_usd(-payout_usd)
            else:
                # Loss: bankroll gains the bet amount
                adjust_bankroll_usd(round(-amount * STARS_TO_USD, 2))
        if amount > 0:
            # Golden hour: boost all game wins
            if golden_hour_end_dt and datetime.now() < golden_hour_end_dt:
                amount = int(round(amount * golden_hour_mult_val))
            # Jackpot: first game win claims the pot
            if active_jackpot_stars > 0:
                jackpot_won = int(active_jackpot_stars)
                active_jackpot_stars = 0
                _jackpot_notify_queue.append((user_id, jackpot_won))
                db.adjust_user_balance(user_id, amount + jackpot_won)
                return True
        db.adjust_user_balance(user_id, amount)
    return True


