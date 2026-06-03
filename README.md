# 🎰 Casino Telegram Bot (v2)

A feature-rich, high-performance Telegram Casino Bot built with Python. This bot provides a seamless and interactive casino experience directly within Telegram, complete with fully functional mini-games, an integrated economy, cryptocurrency support, and multi-language capabilities.

## ✨ Key Features

- **🎮 Extensive Game Library**
  - **Blackjack:** Full point-based Blackjack game.
  - **Mines:** Interactive grid-based Minesweeper gambling.
  - **Coinflip:** Classic Heads or Tails betting.
  - **Predict:** Custom odds-based prediction games.
  - **Point Games:** Telegram's native animated games (Dice, Darts, Basketball, Bowling).
- **💸 Advanced Economy & Cashier**
  - Deposit and withdraw funds using standard balances or cryptocurrency.
  - Fully integrated with **OxaPay** for live Crypto deposits and withdrawals.
- **🌍 Multi-Language Support**
  - Built-in support for English, Russian, German, French, and Chinese.
  - Auto-detects the user's Telegram language preferences.
- **🛡️ Secure & Modular Architecture**
  - **Version 2 Modernization:** The codebase has been refactored into a professional modular structure (`casino_bot/handlers/`, `games/`, etc.), moving away from legacy monolithic designs.
  - **Environment Variables:** All secrets (like your `BOT_TOKEN`) are secured inside a `.env` file.
  - **Robust Logging:** Built-in rotating file handlers keep your server logs clean and prevent storage crashes.

## 📁 Repository Structure

```text
casino v2/
├── bot.py                # Main bot entry point and routing
├── casino_bot/           # Modularized application logic
│   ├── config.py         # Centralized game configurations and multipliers
│   ├── translations/     # Multi-language dictionary and helpers
│   ├── games/            # Shared logic for Blackjack, Predict, etc.
│   └── handlers/         # Specialized Telegram callback handlers
│       ├── cashier_handler.py
│       ├── coinflip_handler.py
│       ├── mines_handler.py
│       └── point_games_handler.py
├── logs/                 # Auto-rotating application logs
├── storage.py            # SQLite database management layer
└── requirements.txt      # Python dependencies
```

## 🚀 Quick Start Guide

### 1. Clone the Repository
```bash
git clone https://github.com/deco94816-design/megatron.git
cd megatron
```

### 2. Set Up the Environment
It is highly recommended to use a virtual environment.
```bash
# Create a virtual environment
python -m venv .venv

# Activate it (Windows)
.venv\Scripts\activate

# Activate it (Mac/Linux)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Your Secrets
1. Create a `.env` file in the root directory.
2. Add your Telegram Bot Token and your Telegram User ID (to grant yourself admin privileges):
```env
BOT_TOKEN=your_telegram_bot_token_here
ADMIN_ID=your_telegram_user_id_here
```
*(Do **not** share your `.env` file or upload it to GitHub!)*

### 4. Run the Bot
```bash
python bot.py
```
Your bot will initialize its SQLite databases, connect to Telegram, and begin processing user commands!

---
*Built with ❤️ for the Telegram gaming community.*
