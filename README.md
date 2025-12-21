# THIS IS A PROJECT FULLY DEVELOPED BY AI, USE IT AT YOUR OWN RISK

# Twitter-Twitch-YouTube Notification Bot

A Python bot that monitors Twitch channels and YouTube channels, automatically posting to Twitter/X when streams go live.

## Features

- 🎮 Monitors multiple Twitch channels via EventSub WebSocket
- 📺 Monitors multiple YouTube channels via polling (60s interval)
- 🐦 Posts customizable notifications to Twitter/X
- 📝 Includes stream title and game in notifications
- 🔧 Easy configuration via environment variables

## Requirements

- Python 3.9+
- Twitch Developer Application (for API credentials)
- Twitter/X Developer Account (for API credentials)

## Account Setup

This bot requires **two Twitter accounts**:

1. **Main Account** - Your primary Twitter account with Developer Portal access
2. **Bot Account** - A separate Twitter account that will post the notifications

### Why Two Accounts?

- The Developer Portal app is created under your **main account**
- The **bot account** is authorized to post tweets using the app's credentials
- This keeps your main account separate from automated posting

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Get Twitch API Credentials

1. Go to [Twitch Developer Console](https://dev.twitch.tv/console)
2. Create a new application
3. Copy the Client ID and generate a Client Secret

### 3. Get YouTube Channel IDs

1. Go to the YouTube channel page you want to monitor
2. View page source (Ctrl+U)
3. Search for `"channelId"` - it looks like `UCxxxxxxxxxxxxxxxxxxxxxxxxxx`
4. Copy the channel ID (starts with UC)

### 4. Get Twitter API Credentials

1. **Main Account Setup:**

   - Go to [Twitter Developer Portal](https://developer.twitter.com/)
   - Create a new project and app
   - Go to "Keys and Tokens" → copy **API Key** and **API Secret**
   - Make sure your app has **Read and Write** permissions

2. **Bot Account Authorization:**
   - Run `twitterVerify.py` to authorize your bot account:
     ```bash
     python twitterVerify.py
     ```
   - Follow the prompts:
     - Log out of Twitter in your browser
     - Log in with your **bot account**
     - Open the authorization URL
     - Authorize the app and copy the PIN
   - Save the generated **Access Token** and **Access Token Secret**

### 5. Configure Environment

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```
# Twitch
TWITCH_CLIENT_ID=your_client_id
TWITCH_CLIENT_SECRET=your_client_secret
TWITCH_CHANNELS=channel1,channel2,channel3
TWITCH_FANNAMES=Fans1,Fans2,Fans3

# YouTube
YOUTUBE_CHANNELS=UCxxxxxxx,UCyyyyyyy
YOUTUBE_SCHEDULED_STREAMS=video_id_1,video_id_2
YOUTUBE_CHECK_INTERVAL=60

# Twitter (API keys from main account's Developer Portal)
TWITTER_API_KEY=your_api_key
TWITTER_API_SECRET=your_api_secret

# Twitter (Access tokens from bot account via twitterVerify.py)
TWITTER_ACCESS_TOKEN=your_bot_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_bot_access_token_secret
```

### 6. (Optional) Customize Notification Messages

**Twitch template:**

```
TWITCH_NOTIFICATION_TEMPLATE={channel} is now live! 🎮\n\n{title}\n\nWatch: https://twitch.tv/{channel}
```

Placeholders: `{channel}`, `{title}`, `{game}`, `{fanname}`

**YouTube template:**

```
YOUTUBE_NOTIFICATION_TEMPLATE={channel} is live on YouTube! 🔴\n\n{title}\n\nhttps://youtube.com/watch?v={video_id}
```

Placeholders: `{channel}`, `{title}`, `{video_id}`

## Usage

### Test Message (Optional)

Verify your Twitter credentials and message formatting:

```bash
python testMsg.py
```

### Run the Bot

```bash
python bot.py
```

The bot will:

1. Open a Twitch authorization URL (complete the auth flow in browser)
2. Connect to Twitch EventSub
3. Start YouTube channel polling (every 60s by default)
4. Post to Twitter when any monitored channel goes live

Press `Ctrl+C` to stop the bot.

## YouTube Scheduled Streams

If a channel has a scheduled/upcoming stream, add its video ID to `YOUTUBE_SCHEDULED_STREAMS` to prevent duplicate notifications when it goes live. The bot caches these IDs on startup.

## Running as a Service (Optional)

For production use, consider running the bot as a background service using:

- **systemd** (Linux)
- **Task Scheduler** (Windows)
- **Docker** (cross-platform)

## License

MIT
