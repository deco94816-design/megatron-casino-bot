"""
Casino Bot — Clean Entry Point
This module provides an alternative entry point that uses the refactored package.
The original 'bot.py' remains the primary entry point until
all modules are fully wired up.
"""
import os
import sys

# Add parent directory to path so imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the original main function
# During the transition period, we delegate to the original file
def main():
    """Start the casino bot."""
    print("Casino Bot — Refactored Package")
    print("================================")
    print("Available modules:")
    print("  casino_bot.config        — Constants & configuration")
    print("  casino_bot.translations  — i18n (en.json, ru.json)")
    print("  casino_bot.utils         — Decorators & helpers")
    print("  casino_bot.games         — Game logic (blackjack, predict, sessions)")
    print("  casino_bot.handlers      — Handler modules (leaderboard)")
    print("  casino_bot.services      — Business logic (balance, events)")
    print()
    
    # For now, run the original
    exec(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bot.py"), encoding="utf-8").read())


if __name__ == "__main__":
    main()
