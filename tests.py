"""
Basic smoke tests for the refactored casino_bot package.
Verifies all modules import correctly and contain expected exports.
"""
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

# Add parent dir to path
sys.path.insert(0, r'c:\Users\Administrator\Downloads\Telegram Desktop')
os.chdir(r'c:\Users\Administrator\Downloads\Telegram Desktop')

passed = 0
failed = 0
total = 0

def test(name, condition, detail=""):
    global passed, failed, total
    total += 1
    if condition:
        passed += 1
        print(f"  ✅ PASS: {name}")
    else:
        failed += 1
        print(f"  ❌ FAIL: {name} — {detail}")


print("=" * 60)
print("Casino Bot Refactoring — Smoke Tests")
print("=" * 60)

# ── Phase 1: Config ──
print("\n📦 Phase 1: Config Module")
try:
    from casino_bot.config import BOT_TOKEN, ADMIN_ID, GAME_CONFIG, MULTIPLIERS
    test("config.py imports", True)
    test("BOT_TOKEN is a string", isinstance(BOT_TOKEN, str))
    test("ADMIN_ID is an int", isinstance(ADMIN_ID, int))
    test("GAME_CONFIG is a dict", isinstance(GAME_CONFIG, dict))
    test("GAME_CONFIG has 'dice'", "dice" in GAME_CONFIG)
    test("MULTIPLIERS is a dict", isinstance(MULTIPLIERS, dict))
except Exception as e:
    test("config.py imports", False, str(e))

# ── Phase 1: Translations ──
print("\n📦 Phase 1: Translations Module")
try:
    from casino_bot.translations import t
    test("translations/__init__.py imports", True)
    result = t("btn_cancel")
    test("t('btn_cancel') returns a string", isinstance(result, str) and len(result) > 0, f"got: {result!r}")

    import json
    with open("casino_bot/translations/en.json", "r", encoding="utf-8") as f:
        en = json.load(f)
    test("en.json loads", isinstance(en, dict))
    test("en.json has 90+ keys", len(en) >= 90, f"got {len(en)} keys")

    with open("casino_bot/translations/ru.json", "r", encoding="utf-8") as f:
        ru = json.load(f)
    test("ru.json loads", isinstance(ru, dict))
    test("ru.json has 100+ keys", len(ru) >= 100, f"got {len(ru)} keys")
except Exception as e:
    test("translations module", False, str(e))

# ── Phase 1: Decorators ──
print("\n📦 Phase 1: Decorators Module")
try:
    from casino_bot.utils.decorators import handle_errors
    test("decorators.py imports", True)
    test("handle_errors is callable", callable(handle_errors))
except Exception as e:
    test("decorators.py imports", False, str(e))

# ── Phase 2: Sessions ──
print("\n📦 Phase 2: Sessions Module")
try:
    from casino_bot.games.sessions import (
        game_sessions, coinflip_sessions, predict_sessions,
        blackjack_sessions, mines_games,
        create_game_session, get_game_session, end_game_session,
        create_bj_session, get_bj_session, end_bj_session,
    )
    test("sessions.py imports", True)
    test("game_sessions is a dict", isinstance(game_sessions, dict))

    # Test CRUD
    create_game_session(999, {"test": True})
    test("create_game_session works", get_game_session(999) == {"test": True})
    end_game_session(999)
    test("end_game_session works", get_game_session(999) is None)
except Exception as e:
    test("sessions.py", False, str(e))

# ── Phase 2: Blackjack ──
print("\n📦 Phase 2: Blackjack Module")
try:
    from casino_bot.games.blackjack import (
        bj_create_deck, bj_card_points, bj_calculate_score, bj_hand_str
    )
    test("blackjack.py imports", True)

    deck = bj_create_deck()
    test("bj_create_deck returns 52 cards", len(deck) == 52, f"got {len(deck)}")
    test("bj_card_points('A') == 11", bj_card_points('A') == 11)
    test("bj_card_points('K') == 10", bj_card_points('K') == 10)
    test("bj_card_points('5') == 5", bj_card_points('5') == 5)

    score = bj_calculate_score([{'value': 'A', 'suit': '♠'}, {'value': 'K', 'suit': '♥'}])
    test("bj_calculate_score([A,K]) == 21", score == 21, f"got {score}")
except Exception as e:
    test("blackjack.py", False, str(e))

# ── Phase 2: Predict ──
print("\n📦 Phase 2: Predict Module")
try:
    from casino_bot.games.predict import predict_get_multiplier
    test("predict.py imports", True)
except Exception as e:
    test("predict.py", False, str(e))

# ── Phase 3: Leaderboard Handler ──
print("\n📦 Phase 3: Leaderboard Handler")
try:
    from casino_bot.handlers.leaderboard import build_lb_caption, build_lb_keyboard
    test("leaderboard.py imports", True)
    caption = build_lb_caption("wins")
    test("build_lb_caption('wins') returns text", len(caption) > 50, f"got {len(caption)} chars")
    kb = build_lb_keyboard()
    test("build_lb_keyboard() returns markup", kb is not None)
except Exception as e:
    test("leaderboard.py", False, str(e))

# ── Phase 4: Services ──
print("\n📦 Phase 4: Services")
try:
    from casino_bot.services.events import (
        is_golden_hour, get_golden_hour_multiplier,
        is_cashback_active, get_cashback_rate,
    )
    test("events.py imports", True)
    test("is_golden_hour() returns bool", isinstance(is_golden_hour(), bool))
    test("get_golden_hour_multiplier() returns float", isinstance(get_golden_hour_multiplier(), float))
except Exception as e:
    test("events.py", False, str(e))

# ── Phase 5: Main file still works ──
print("\n📦 Phase 5: Original main file")
try:
    import py_compile
    py_compile.compile("bot.py", doraise=True)
    test("bot.py compiles", True)
except Exception as e:
    test("bot.py compiles", False, str(e))

# ── Summary ──
print("\n" + "=" * 60)
print(f"Results: {passed}/{total} passed, {failed} failed")
print("=" * 60)

if failed > 0:
    print("\n⚠️  Some tests failed — review and fix before running the bot.")
else:
    print("\n✅ All tests passed! The refactored package is ready.")
