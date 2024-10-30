```markdown
# Mostaql Projects Telegram Bot

A Telegram bot that automatically scrapes and notifies subscribers about new projects posted on Mostaql.com.

## Features

- 🔄 Automatic project updates every 15 minutes
- 📢 Instant notifications for new projects
- 📝 Detailed project information including:
  - Project name and description
  - Budget and duration
  - Number of offers
  - Average offer price
- 👥 Subscriber management system
- 🔐 Secure token handling
- 🚀 GitHub Actions integration

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd mostaql-projects-bot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Environment Setup

1. Create a Telegram bot using [@BotFather](https://t.me/botfather)
2. Copy your bot token
3. Set environment variable:
   - Local development: Create `.env` file with:
     ```
     TELEGRAM_TOKEN=your_bot_token_here
     ```
   - GitHub Actions: Add `TELEGRAM_TOKEN` to repository secrets

## Usage

1. Start the bot:
```bash
python bot.py
```

2. In Telegram:
   - Search for your bot
   - Send `/start` to subscribe
   - Receive automatic project updates

## Project Structure

```
mostaql-projects-bot/
├── bot.py              # Main bot logic
├── requirements.txt    # Project dependencies
├── subscribers.json    # Subscriber data storage
├── .env               # Environment variables (local)
└── .github/workflows/ # GitHub Actions configuration
```

## Dependencies

- python-telegram-bot==13.7
- requests==2.28.2
- beautifulsoup4==4.11.2
- pandas==1.5.3
- python-dotenv==1.0.0

## GitHub Actions

The bot runs automatically every 15 minutes using GitHub Actions. Configuration can be found in `.github/workflows/bot-scheduler.yml`.

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details
```
