"""
Twitter-Twitch Notification Bot

A simple bot that monitors a Twitch channel and posts to Twitter/X
when the stream goes live.
"""

import asyncio
import os
import re
import signal
import sys

import aiohttp

from dotenv import load_dotenv
import tweepy
from twitchAPI.twitch import Twitch
from twitchAPI.oauth import CodeFlow
from twitchAPI.eventsub.websocket import EventSubWebsocket
from twitchAPI.object.eventsub import StreamOnlineEvent
from twitchAPI.helper import first
from twitchAPI.oauth import UserAuthenticator
from twitchAPI.type import AuthScope

# Load environment variables
load_dotenv()

# General streamer configuration (by index)
FANNAMES_RAW = os.getenv("FANNAMES", "")
FANNAMES = [fn.strip() for fn in FANNAMES_RAW.split(",") if fn.strip()]
DISPLAY_NAMES_RAW = os.getenv("DISPLAY_NAMES", "")
DISPLAY_NAMES = [dn.strip() for dn in DISPLAY_NAMES_RAW.split(",") if dn.strip()]

# Twitch credentials
TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
TWITCH_CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET")
TWITCH_CHANNELS_RAW = os.getenv("TWITCH_CHANNELS", "")
TWITCH_CHANNELS = [ch.strip() for ch in TWITCH_CHANNELS_RAW.split(",") if ch.strip()]

# Build Twitch channel -> index mapping
TWITCH_CHANNEL_INDEX = {ch.lower(): i for i, ch in enumerate(TWITCH_CHANNELS)}

# YouTube credentials
YOUTUBE_CHANNELS_RAW = os.getenv("YOUTUBE_CHANNELS", "")
YOUTUBE_CHANNELS = [ch.strip() for ch in YOUTUBE_CHANNELS_RAW.split(",") if ch.strip()]
YOUTUBE_SCHEDULED_STREAMS_RAW = os.getenv("YOUTUBE_SCHEDULED_STREAMS", "")
YOUTUBE_SCHEDULED_STREAMS = [vid.strip() for vid in YOUTUBE_SCHEDULED_STREAMS_RAW.split(",") if vid.strip()]
YOUTUBE_CHECK_INTERVAL = int(os.getenv("YOUTUBE_CHECK_INTERVAL", "60"))

# Build YouTube channel -> index mapping
YOUTUBE_CHANNEL_INDEX = {ch: i for i, ch in enumerate(YOUTUBE_CHANNELS)}

# Twitter credentials
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

# Meta Threads credentials
THREADS_ACCESS_TOKEN = os.getenv("THREADS_ACCESS_TOKEN")
THREADS_USER_ID = os.getenv("THREADS_USER_ID")


def get_streamer_info(index: int) -> tuple[str, str]:
    """Get fanname and display name for a streamer by index."""
    fanname = FANNAMES[index] if index < len(FANNAMES) else "fans"
    display_name = DISPLAY_NAMES[index] if index < len(DISPLAY_NAMES) else f"Streamer{index}"
    return fanname, display_name


# Notification templates
DEFAULT_TWITCH_TEMPLATE = "{display_name} is now live on Twitch! 🎮\n\n📺 {title}\n🎯 Playing: {game}\n\n👉 https://twitch.tv/{channel}"
TWITCH_NOTIFICATION_TEMPLATE = os.getenv("TWITCH_NOTIFICATION_TEMPLATE", os.getenv("NOTIFICATION_TEMPLATE", DEFAULT_TWITCH_TEMPLATE)).replace("\\n", "\n")

DEFAULT_YOUTUBE_TEMPLATE = "{display_name} is now live on YouTube! 🔴\n\n📺 {title}\n\n👉 https://youtube.com/watch?v={video_id}"
YOUTUBE_NOTIFICATION_TEMPLATE = os.getenv("YOUTUBE_NOTIFICATION_TEMPLATE", DEFAULT_YOUTUBE_TEMPLATE).replace("\\n", "\n")

TWITCH_THREADS_TEMPLATE = os.getenv("TWITCH_THREADS_TEMPLATE", "").replace("\\n", "\n")
YOUTUBE_THREADS_TEMPLATE = os.getenv("YOUTUBE_THREADS_TEMPLATE", "").replace("\\n", "\n")


def validate_env():
    """Validate that all required environment variables are set."""
    required = [
        ("TWITCH_CLIENT_ID", TWITCH_CLIENT_ID),
        ("TWITCH_CLIENT_SECRET", TWITCH_CLIENT_SECRET),
        ("TWITCH_CHANNELS", TWITCH_CHANNELS_RAW),
        ("TWITTER_API_KEY", TWITTER_API_KEY),
        ("TWITTER_API_SECRET", TWITTER_API_SECRET),
        ("TWITTER_ACCESS_TOKEN", TWITTER_ACCESS_TOKEN),
        ("TWITTER_ACCESS_TOKEN_SECRET", TWITTER_ACCESS_TOKEN_SECRET),
    ]
    
    missing = [name for name, value in required if not value]
    
    if missing:
        print("❌ Missing required environment variables:")
        for name in missing:
            print(f"   - {name}")
        print("\nPlease copy .env.example to .env and fill in your credentials.")
        sys.exit(1)

def post_tweet(message: str) -> bool:
    """Send a tweet using API v2 (works with Free tier)"""
    try:
        # Create v2 Client (this works with Free tier!)
        client = tweepy.Client(
            consumer_key=TWITTER_API_KEY,
            consumer_secret=TWITTER_API_SECRET,
            access_token=TWITTER_ACCESS_TOKEN,
            access_token_secret=TWITTER_ACCESS_TOKEN_SECRET
        )
        
        # Post the tweet
        response = client.create_tweet(text=message)
        
        tweet_id = response.data['id']
        print("✓ Tweet posted successfully!")
        print(f"  Tweet ID: {tweet_id}")
        print(f"  Content: {message}")
        
        return tweet_id
        
    except tweepy.errors.Forbidden as e:
        print(f"✗ Permission error: {e}")
        print("  Make sure your app has 'Read and Write' permissions")
    except tweepy.errors.Unauthorized as e:
        print(f"✗ Authentication error: {e}")
        print("  Check your API credentials")
    except tweepy.errors.TweepyException as e:
        print(f"✗ Twitter API error: {e}")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
    return None


async def post_threads_meta(message: str) -> bool:
    """Post to Meta's Threads platform using the official API."""
    if not THREADS_ACCESS_TOKEN or not THREADS_USER_ID or not message:
        return False
        
    print(f"[THREADS] Posting to Meta Threads...")
    
    base_url = f"https://graph.threads.net/v1.0/{THREADS_USER_ID}"
    headers = {"Authorization": f"Bearer {THREADS_ACCESS_TOKEN}"}
    
    async with aiohttp.ClientSession() as session:
        try:
            # 1. Create a media container
            print("   Step 1: Creating media container...")
            async with session.post(
                f"{base_url}/threads",
                params={
                    "media_type": "TEXT",
                    "text": message,
                    "access_token": THREADS_ACCESS_TOKEN
                }
            ) as resp:
                data = await resp.json()
                if resp.status != 200:
                    print(f"   ✗ Container creation failed: {data}")
                    return False
                
                creation_id = data.get("id")
                if not creation_id:
                    print("   ✗ No creation ID returned")
                    return False

            # 2. Publish the container
            print("   Step 2: Publishing container...")
            async with session.post(
                f"{base_url}/threads_publish",
                params={
                    "creation_id": creation_id,
                    "access_token": THREADS_ACCESS_TOKEN
                }
            ) as resp:
                data = await resp.json()
                if resp.status != 200:
                    print(f"   ✗ Publishing failed: {data}")
                    return False
                
                print("✓ Successfully posted to Meta Threads!")
                print(f"  Threads Post ID: {data.get('id')}")
                return True
                
        except Exception as e:
            print(f"   ✗ Error posting to Meta Threads: {e}")
            return False


class YouTubeMonitor:
    """Monitors YouTube channels for live streams."""
    
    def __init__(self, channels: list[str], scheduled_streams: list[str]):
        self.channels = channels
        self.scheduled_streams = set(scheduled_streams)  # Pre-cached scheduled stream IDs
        self.known_video_ids: set[str] = set(scheduled_streams)  # Cache of known video IDs
        self.running = False
    
    async def check_channel_live(self, session: aiohttp.ClientSession, channel_id: str) -> tuple[str | None, str | None, str | None]:
        """Check if a YouTube channel is live by fetching the /live page.
        
        Returns (video_id, channel_name, title) if live, else (None, None, None).
        """
        url = f"https://www.youtube.com/channel/{channel_id}/live"
        
        try:
            async with session.get(url, allow_redirects=True) as response:
                if response.status != 200:
                    return None, None, None
                
                final_url = str(response.url)
                html = await response.text()
                
                # Check if redirected to a video page
                video_match = re.search(r'watch\?v=([a-zA-Z0-9_-]{11})', final_url)
                if not video_match:
                    # Try to find video ID in the page content (for embedded player)
                    video_match = re.search(r'"videoId":"([a-zA-Z0-9_-]{11})"', html)
                
                if not video_match:
                    return None, None, None
                
                video_id = video_match.group(1)
                
                # Extract channel name
                channel_name_match = re.search(r'"ownerChannelName":"([^"]+)"', html)
                channel_name = channel_name_match.group(1) if channel_name_match else channel_id
                
                # Extract title
                title_match = re.search(r'"title":"([^"]+)"', html)
                title = title_match.group(1) if title_match else "Live Stream"

                # Check playability status and live status
                if '"playabilityStatus":{"status":"OK"' not in html :
                    print(f"⚠️ Non-live stream detected: {channel_name}, {title}")
                    return None, None, None
                
                return video_id, channel_name, title
                
        except Exception as e:
            print(f"⚠️ Error checking YouTube channel {channel_id}: {e}")
            return None, None, None
    
    async def check_all_channels(self):
        """Check all YouTube channels for live streams."""
        if not self.channels:
            return
        
        async with aiohttp.ClientSession(headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }) as session:
            for channel_id in self.channels:
                video_id, channel_name, title = await self.check_channel_live(session, channel_id)
                
                if video_id and video_id not in self.known_video_ids:
                    print(f"\n🔴 YouTube Live detected: {channel_name}")
                    print(f"   Video ID: {video_id}")
                    print(f"   Title: {title}")
                    
                    # Add to cache
                    self.known_video_ids.add(video_id)
                    
                    # Get streamer info by index
                    index = YOUTUBE_CHANNEL_INDEX.get(channel_id, 0)
                    fanname, display_name = get_streamer_info(index)
                    
                    # Format and post notification
                    message = YOUTUBE_NOTIFICATION_TEMPLATE.format(
                        channel=channel_name,
                        display_name=display_name,
                        fanname=fanname,
                        title=title,
                        video_id=video_id,
                    )
                    
                    print(f"📝 Posting YouTube notification:\n{message}\n")
                    post_tweet(message)
                    
                    # Post to Meta Threads if template exists
                    if YOUTUBE_THREADS_TEMPLATE:
                        threads_message = YOUTUBE_THREADS_TEMPLATE.format(
                            channel=channel_name,
                            display_name=display_name,
                            fanname=fanname,
                            title=title,
                            video_id=video_id,
                        )
                        print(f"📝 Posting YouTube to Meta Threads:\n{threads_message}\n")
                        asyncio.create_task(post_threads_meta(threads_message))
    
    async def start(self):
        """Start the YouTube monitoring loop."""
        if not self.channels:
            print("ℹ️ No YouTube channels configured, skipping YouTube monitoring.")
            return
        
        print(f"📺 Starting YouTube monitor for {len(self.channels)} channel(s)...")
        print(f"   Channels: {', '.join(self.channels)}")
        if self.scheduled_streams:
            print(f"   Pre-cached scheduled streams: {', '.join(self.scheduled_streams)}")
        print(f"   Check interval: {YOUTUBE_CHECK_INTERVAL}s")
        
        self.running = True
        
        while self.running:
            try:
                await self.check_all_channels()
            except Exception as e:
                print(f"⚠️ YouTube check error: {e}")
            
            await asyncio.sleep(YOUTUBE_CHECK_INTERVAL)
    
    def stop(self):
        """Stop the YouTube monitoring loop."""
        self.running = False


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
            stream_data = await first(self.twitch.get_streams(user_login=[channel_name]))
            
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
        
        # Get streamer info by index
        index = TWITCH_CHANNEL_INDEX.get(channel_name.lower(), 0)
        fanname, display_name = get_streamer_info(index)
        
        # Format and post the notification
        message = TWITCH_NOTIFICATION_TEMPLATE.format(
            channel=channel_name,
            display_name=display_name,
            title=title,
            game=game,
            fanname=fanname,
        )
        
        print(f"📝 Posting Twitch notification:\n{message}\n")
        post_tweet(message)
        
        # Post to Meta Threads if template exists
        if TWITCH_THREADS_TEMPLATE:
            threads_message = TWITCH_THREADS_TEMPLATE.format(
                channel=channel_name,
                display_name=display_name,
                title=title,
                game=game,
                fanname=fanname,
            )
            print(f"📝 Posting Twitch to Meta Threads:\n{threads_message}\n")
            asyncio.create_task(post_threads_meta(threads_message))
    
    async def start(self):
        """Start the Twitch EventSub listener."""
        print("🚀 Starting Twitter-Twitch Notification Bot...")
        print(f"📋 Monitoring {len(self.channels)} channel(s): {', '.join(self.channels)}")
        
        # Initialize Twitch API
        self.twitch = await Twitch(TWITCH_CLIENT_ID, TWITCH_CLIENT_SECRET)
        target_scope = [AuthScope.USER_READ_EMAIL]
        code_flow = CodeFlow(self.twitch, target_scope)
        code, url = await code_flow.get_code()
        print(url)  # visit this url and complete the flow
        token, refresh = await code_flow.wait_for_auth_complete()
        print(f"🔐 User authentication successful!")
        print(f"   Token received: {token[:20]}...")
        await self.twitch.set_user_authentication(token, target_scope, refresh)

        # Get broadcaster IDs for all channels
        users_data = []
        async for user in self.twitch.get_users(logins=self.channels):
            users_data.append(user)
        
        if not users_data:
            print("❌ Could not find any Twitch channels")
            sys.exit(1)
        
        for user in users_data:
            self.broadcaster_ids[user.login] = user.id
            print(f"✅ Found channel: {user.login} (ID: {user.id})")
        
        # Check for missing channels
        found_logins = {u.login.lower() for u in users_data}
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
    youtube_monitor = YouTubeMonitor(YOUTUBE_CHANNELS, YOUTUBE_SCHEDULED_STREAMS)
    youtube_task = None
    
    # Handle graceful shutdown
    loop = asyncio.get_event_loop()
    
    def signal_handler():
        youtube_monitor.stop()
        asyncio.create_task(notifier.stop())
        loop.stop()
    
    # Set up signal handlers for graceful shutdown
    if sys.platform != "win32":
        loop.add_signal_handler(signal.SIGINT, signal_handler)
        loop.add_signal_handler(signal.SIGTERM, signal_handler)
    
    try:
        await notifier.start()
        
        # Start YouTube monitor as a background task
        if YOUTUBE_CHANNELS:
            youtube_task = asyncio.create_task(youtube_monitor.start())
        
        # Keep running until interrupted
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        youtube_monitor.stop()
        await notifier.stop()
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {e}")
        youtube_monitor.stop()
        await notifier.stop()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
