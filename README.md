# 🤖 Binance Alert Bot

A Telegram bot for cryptocurrency price monitoring with customizable alerts and real-time notifications.

## ✨ Features

- 💰 **Price Alerts** - Get notified when price reaches your target level (above/below)
- 📊 **Percentage Alerts** - Track price changes by percentage (growth/decline)
- 💹 **Live Prices** - Check current prices for popular crypto pairs
- 🔔 **Smart Notifications** - Automatic monitoring with instant Telegram alerts
- 🎯 **Custom Pairs** - Support for any trading pair available on Binance
- 🎨 **Clean Interface** - Intuitive inline keyboard navigation
- 🗑️ **Easy Management** - View and delete your alerts anytime

## 🚀 Quick Start
```bash
# Clone repository
git clone https://github.com/yourusername/binance-alert-bot.git
cd binance-alert-bot

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Add your BOT_TOKEN to .env

# Run the bot
python main.py
```

## 📋 Requirements

- Python 3.9+
- Telegram Bot Token (get from [@BotFather](https://t.me/BotFather))

## 📱 How It Works

1. **Create Alert** - Choose a crypto pair and set your target
2. **Select Type**:
   - 🚀 Price above target
   - 📉 Price below target
   - 📈 Growth by percentage
   - 📉 Decline by percentage
3. **Get Notified** - Receive instant Telegram message when conditions are met

## 🎯 Alert Types

| Type | Description | Example |
|------|-------------|---------|
| Price Above | Alert when price exceeds target | BTC > $70,000 |
| Price Below | Alert when price drops below target | ETH < $3,000 |
| Percentage Growth | Alert on X% increase | SOL +5% |
| Percentage Decline | Alert on X% decrease | BNB -3% |

## 🛠️ Tech Stack

- **Backend**: Python 3.9+
- **Bot Framework**: python-telegram-bot 20.7
- **API**: Binance Public API
- **Storage**: JSON file-based
- **Async**: asyncio for background monitoring

## 📁 Project Structure
```
binance-alert-bot/
├── main.py              # Main bot logic and handlers
├── binance_api.py       # Binance API integration
├── alerts_manager.py    # Alert storage management
├── requirements.txt     # Python dependencies
├── .env                 # Environment variables (not in repo)
└── alerts.json         # Alert storage (created on first run)
```

## 🔧 Configuration

Create `.env` file with:
```env
BOT_TOKEN=your_telegram_bot_token_here
ADMIN_ID=your_telegram_user_id (optional)
```

## 📝 Commands

- `/start` - Show main menu
- `/show_alerts` - View all your active alerts
- `/help` - Display help information

## 🎨 Screenshots

*(Add screenshots here when deploying)*

## 🚧 Roadmap

- [ ] Database integration (PostgreSQL/MongoDB)
- [ ] Price charts generation
- [ ] Multiple alerts per pair
- [ ] Historical data analysis
- [ ] Group notifications support
- [ ] Technical indicators (RSI, MACD)
- [ ] Portfolio tracking

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest features
- Submit pull requests

## 📄 License

MIT License - Free for personal and commercial use

## ⚠️ Disclaimer

This bot is for informational purposes only. Cryptocurrency trading carries risk. Always do your own research before making investment decisions.

---

Made with ❤️ for the crypto community

⭐ Star this repo if you find it useful!
