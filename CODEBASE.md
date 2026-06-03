# Casino Bot Codebase Overview

This document provides a comprehensive overview of the refactored and cleaned-up codebase for the Telegram Casino Bot.

## Core Application Files

* **`bot.py`**  
  The main monolithic entry point of the bot (formerly `casino v5 (1).py`). It contains the Telegram bot initialization, main event loop, and currently holds many of the route handlers and game logics. It is actively being refactored to delegate to the modular `casino_bot` package.

* **`launch_bot.py`**  
  A robust process manager script that launches `bot.py` and automatically restarts it if it crashes. It monitors the bot process and provides a safety net for production deployment.

* **`run_bot.bat`**  
  A simple Windows batch script used to start the bot via `launch_bot.py` while ensuring the virtual environment is correctly used.

## Databases & Storage

* **`bot_data.db`** (formerly `casino_data.db`)  
  The main SQLite database storing persistent data: users, balances, game history, deposits, withdrawals, referrals, and support tickets.
* **`storage.py`**  
  The database access layer wrapping SQLite operations for `bot_data.db` with thread-safe locks (`threading.RLock`).
* **`bot_network.db`** & **`bot_network.py`**  
  Handles multi-bot networks, shared blacklists, and cross-bot administrative synchronization.
* **`templates.db`**  
  Stores customizable text templates for bot messages.
* **`emoji_mappings.db`**  
  Stores custom emoji mappings for the dynamic emoji replacement system.

## Utilities & Integrations

* **`languages.py`**  
  Legacy translation utilities for multi-language support (currently being migrated to JSON-based translations in `casino_bot/translations/`).
* **`oxapay.py`**  
  Integration for OxaPay crypto payments, handling deposit invoice generation and payment verification.
* **`streaming_funcs.py` & `streaming_setup.py`**  
  Provides the typing/streaming text effect used when the bot replies to messages, enhancing the user experience.
* **`tests.py`**  
  Smoke tests to verify the integrity and correctness of the newly refactored `casino_bot` modules.

## The `casino_bot` Package (New Modular Architecture)

The codebase is migrating from the monolithic `bot.py` into a clean, modular package structure located in the `casino_bot/` directory:

* **`config.py`**: Centralized constants, bot token, admin lists, and game configurations.
* **`main.py`**: The future clean entry point for the modular application.
* **`translations/`**: Contains `en.json`, `ru.json`, and an `__init__.py` to handle localization cleanly.
* **`utils/`**: Shared utilities, currently housing the `decorators.py` (e.g., `@handle_errors`).
* **`games/`**: Pure game logic separated from Telegram API concerns:
  * `sessions.py`: Centralized in-memory session management.
  * `blackjack.py`: Card deck logic, scoring, and PIL-based table image generation.
  * `predict.py`: Number prediction game logic and keyboard builder.
* **`handlers/`**: Telegram update handlers (e.g., `leaderboard.py` for leaderboard interactions).
* **`services/`**: Core business logic modules:
  * `balance.py`: Balance operations (get/set/adjust).
  * `events.py`: Global event state management (Golden Hour, Cashback, Rain).

## Static Assets

* **`lb_wins.jpg`, `lb_money.png`, `lb_active.jpg`, `lb_roller.jpg`**  
  Static images used for the image-based dynamic leaderboard system.

## Documentation

* **`ARCHITECTURE.md`**  
  Deep analysis of the original codebase structure, identifying technical debt and serving as the foundation for the current refactoring process.
* **`SETUP.md`**  
  Deployment instructions and environment setup guide.
