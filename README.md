# THIS IS A PROJECT FULLY DEVELOPED BY AI, USE IT AT YOUR OWN RISK

# Twitter-Twitch Notification Bot

A simple Python bot that monitors a Twitch channel and automatically posts to Twitter/X when the stream goes live.

## Features

- 🎮 Monitors multiple Twitch channels for stream start events via EventSub WebSocket
- 🐦 Posts customizable notifications to Twitter/X
- 📝 Includes stream title and game in notifications
- 🔧 Easy configuration via environment variables

## Requirements

- Python 3.9+
- Twitch Developer Application (for API credentials)
- Twitter/X Developer Account (for API credentials)

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Get API Credentials

**Twitch:**

1. Go to [Twitch Developer Console](https://dev.twitch.tv/console)
2. Create a new application
3. Copy the Client ID and generate a Client Secret

**Twitter/X:**

1. Go to [Twitter Developer Portal](https://developer.twitter.com/)
2. Create a new project and app
3. Go to "Keys and Tokens" and generate a **Bearer Token**
4. Make sure your app has **Read and Write** permissions

### 3. Configure Environment

Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```
TWITCH_CLIENT_ID=your_client_id
TWITCH_CLIENT_SECRET=your_client_secret
TWITCH_CHANNELS=channel1,channel2,channel3

TWITTER_BEARER_TOKEN=your_bearer_token
```

### 4. (Optional) Customize Notification Message

You can customize the notification template in `.env`:

```
NOTIFICATION_TEMPLATE={channel} is now live! 🎮\n\n{title}\n\nWatch: https://twitch.tv/{channel}
```

Available placeholders:

- `{channel}` - Twitch channel name
- `{title}` - Stream title
- `{game}` - Game being played

## Usage

```bash
python bot.py
```

The bot will:

1. Connect to Twitch EventSub
2. Listen for stream start events from all configured channels
3. Post to Twitter when any monitored channel goes live

Press `Ctrl+C` to stop the bot.

## Running as a Service (Optional)

For production use, consider running the bot as a background service using:

- **systemd** (Linux)
- **Task Scheduler** (Windows)
- **Docker** (cross-platform)

## License

MIT
