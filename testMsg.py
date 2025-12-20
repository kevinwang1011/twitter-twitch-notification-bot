"""
Test script to verify Twitter message formatting.
Sends a test tweet to verify newlines and template work correctly.
"""

import os
from dotenv import load_dotenv
import tweepy

# Load environment variables
load_dotenv()

# Twitter credentials
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

# Notification template
DEFAULT_TEMPLATE = "{channel} is now live on Twitch! 🎮\n\n📺 {title}\n🎯 Playing: {game}\n\n👉 https://twitch.tv/{channel}"
NOTIFICATION_TEMPLATE = os.getenv("NOTIFICATION_TEMPLATE", DEFAULT_TEMPLATE).replace("\\n", "\n")


def preview_message():
    """Preview the formatted message without sending."""
    test_data = {
        "channel": "TestChannel",
        "title": "Test Stream Title",
        "game": "Test Game",
        "fanname": "TestFans",
    }
    
    message = NOTIFICATION_TEMPLATE.format(**test_data)
    
    print("=" * 50)
    print("MESSAGE PREVIEW:")
    print("=" * 50)
    print(message)
    print("=" * 50)
    print(f"\nCharacter count: {len(message)}/280")
    print(f"Newlines detected: {message.count(chr(10))}")
    
    return message


def send_test_tweet():
    """Send a test tweet to verify formatting."""
    try:
        client = tweepy.Client(
            consumer_key=TWITTER_API_KEY,
            consumer_secret=TWITTER_API_SECRET,
            access_token=TWITTER_ACCESS_TOKEN,
            access_token_secret=TWITTER_ACCESS_TOKEN_SECRET
        )
        
        # Use a simple test message with newlines
        test_message = "🧪 Test message from bot!\n\nLine 2 here\nLine 3 here\n\n✅ If you see proper line breaks, it works!"
        
        print("\n📤 Sending test tweet...")
        print("-" * 50)
        print(test_message)
        print("-" * 50)
        
        response = client.create_tweet(text=test_message)
        
        print(f"\n✅ Tweet posted successfully!")
        print(f"   Tweet ID: {response.data['id']}")
        print(f"   View at: https://twitter.com/i/status/{response.data['id']}")
        
        return True
        
    except tweepy.errors.Forbidden as e:
        print(f"❌ Permission error: {e}")
    except tweepy.errors.Unauthorized as e:
        print(f"❌ Authentication error: {e}")
    except tweepy.errors.TweepyException as e:
        print(f"❌ Twitter API error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    return False


if __name__ == "__main__":
    print("\n🧪 Twitter Message Test Script\n")
    
    # First preview the template
    preview_message()
    
    # Ask if user wants to send a test tweet
    print("\n" + "=" * 50)
    choice = input("\nSend a test tweet? (y/n): ").strip().lower()
    
    if choice == 'y':
        send_test_tweet()
    else:
        print("👍 Preview only - no tweet sent.")
