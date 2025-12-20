"""
Twitter-Twitch Notification Bot

A simple bot that monitors a Twitch channel and posts to Twitter/X
when the stream goes live.
"""

import asyncio
import os
import signal
import sys

from dotenv import load_dotenv
import tweepy
from twitchAPI.twitch import Twitch
from twitchAPI.eventsub.websocket import EventSubWebsocket
from twitchAPI.object.eventsub import StreamOnlineEvent
from twitchAPI.type import AuthScope

# Load environment variables
load_dotenv()

# Twitch credentials
TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
TWITCH_CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET")
TWITCH_CHANNELS_RAW = os.getenv("TWITCH_CHANNELS", "")
TWITCH_CHANNELS = [ch.strip() for ch in TWITCH_CHANNELS_RAW.split(",") if ch.strip()]

# Twitter credentials
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")

# Notification template
DEFAULT_TEMPLATE = "{channel} is now live on Twitch! 🎮\n\n📺 {title}\n🎯 Playing: {game}\n\n👉 https://twitch.tv/{channel}"
NOTIFICATION_TEMPLATE = os.getenv("NOTIFICATION_TEMPLATE", DEFAULT_TEMPLATE)


def validate_env():
    """Validate that all required environment variables are set."""
    required = [
        ("TWITCH_CLIENT_ID", TWITCH_CLIENT_ID),
        ("TWITCH_CLIENT_SECRET", TWITCH_CLIENT_SECRET),
        ("TWITCH_CHANNELS", TWITCH_CHANNELS_RAW),
        ("TWITTER_BEARER_TOKEN", TWITTER_BEARER_TOKEN),
    ]
    
    missing = [name for name, value in required if not value]
    
    if missing:
        print("❌ Missing required environment variables:")
        for name in missing:
            print(f"   - {name}")
        print("\nPlease copy .env.example to .env and fill in your credentials.")
        sys.exit(1)


def get_twitter_client() -> tweepy.Client:
    """Create and return a Twitter API client using Bearer Token."""
    return tweepy.Client(bearer_token=TWITTER_BEARER_TOKEN)


def post_tweet(message: str) -> bool:
    """Post a tweet with the given message."""
    try:
        client = get_twitter_client()
        response = client.create_tweet(text=message)
        print(f"✅ Tweet posted successfully! Tweet ID: {response.data['id']}")
        return True
    except Exception as e:
        print(f"❌ Failed to post tweet: {e}")
        return False


class TwitchNotifier:
    """Handles Twitch EventSub and stream notifications."""
    
    def __init__(self, channels: list[str]):
        self.channels = channels
        self.twitch: Twitch = None
        self.eventsub: EventSubWebsocket = None
        self.broadcaster_ids: dict[str, str] = {}  # channel_name -> broadcaster_id
    
    async def on_stream_online(self, event: StreamOnlineEvent):
        """Callback when the monitored channel goes live."""
        channel_name = event.event.broadcaster_user_login
        print(f"\n🎬 Stream started: {channel_name}")
        
        # Get stream info for the notification
        try:
            streams = await self.twitch.get_streams(user_login=[channel_name])
            stream_data = streams.data[0] if streams.data else None
            
            if stream_data:
                title = stream_data.title
                game = stream_data.game_name or "Unknown"
            else:
                title = "Live now!"
                game = "Unknown"
        except Exception as e:
            print(f"⚠️ Could not fetch stream info: {e}")
            title = "Live now!"
            game = "Unknown"
        
        # Format and post the notification
        message = NOTIFICATION_TEMPLATE.format(
            channel=channel_name,
            title=title,
            game=game,
        )
        
        print(f"📝 Posting notification:\n{message}\n")
        post_tweet(message)
    
    async def start(self):
        """Start the Twitch EventSub listener."""
        print("🚀 Starting Twitter-Twitch Notification Bot...")
        print(f"📋 Monitoring {len(self.channels)} channel(s): {', '.join(self.channels)}")
        
        # Initialize Twitch API
        self.twitch = await Twitch(TWITCH_CLIENT_ID, TWITCH_CLIENT_SECRET)
        
        # Get broadcaster IDs for all channels
        users = await self.twitch.get_users(logins=self.channels)
        if not users.data:
            print("❌ Could not find any Twitch channels")
            sys.exit(1)
        
        for user in users.data:
            self.broadcaster_ids[user.login] = user.id
            print(f"✅ Found channel: {user.login} (ID: {user.id})")
        
        # Check for missing channels
        found_logins = {u.login.lower() for u in users.data}
        missing = [ch for ch in self.channels if ch.lower() not in found_logins]
        if missing:
            print(f"⚠️ Could not find channels: {', '.join(missing)}")
        
        # Set up EventSub WebSocket
        self.eventsub = EventSubWebsocket(self.twitch)
        self.eventsub.start()
        
        # Subscribe to stream.online events for all channels
        for channel_name, broadcaster_id in self.broadcaster_ids.items():
            await self.eventsub.listen_stream_online(
                broadcaster_user_id=broadcaster_id,
                callback=self.on_stream_online,
            )
            print(f"👀 Subscribed to: {channel_name}")
        
        print(f"\n✅ Now monitoring {len(self.broadcaster_ids)} channel(s) for stream start events...")
        print("Press Ctrl+C to stop.\n")
    
    async def stop(self):
        """Stop the EventSub listener and clean up."""
        print("\n🛑 Stopping bot...")
        
        if self.eventsub:
            await self.eventsub.stop()
        
        if self.twitch:
            await self.twitch.close()
        
        print("👋 Goodbye!")


async def main():
    """Main entry point."""
    validate_env()
    
    notifier = TwitchNotifier(TWITCH_CHANNELS)
    
    # Handle graceful shutdown
    loop = asyncio.get_event_loop()
    
    def signal_handler():
        asyncio.create_task(notifier.stop())
        loop.stop()
    
    # Set up signal handlers for graceful shutdown
    if sys.platform != "win32":
        loop.add_signal_handler(signal.SIGINT, signal_handler)
        loop.add_signal_handler(signal.SIGTERM, signal_handler)
    
    try:
        await notifier.start()
        
        # Keep running until interrupted
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        await notifier.stop()
    except Exception as e:
        print(f"❌ Error: {e}")
        await notifier.stop()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
