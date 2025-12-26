import asyncio
import os
from dotenv import load_dotenv
from bot import post_threads_meta

# Load environment variables
load_dotenv()

# Meta Threads credentials
THREADS_ACCESS_TOKEN = os.getenv("THREADS_ACCESS_TOKEN")
THREADS_USER_ID = os.getenv("THREADS_USER_ID")

# Notification templates
DEFAULT_TEMPLATE = "{display_name} is now live on Twitch! 🎮\n\n📺 {title}\n🎯 Playing: {game}\n\n👉 https://twitch.tv/{channel}"
THREADS_TEMPLATE = os.getenv("TWITCH_THREADS_TEMPLATE", DEFAULT_TEMPLATE).replace("\\n", "\n")

def preview_message():
    """Preview the formatted message without sending."""
    test_data = {
        "channel": "TestChannel",
        "display_name": "TestStreamer",
        "title": "Test Stream Title",
        "game": "Test Game",
        "fanname": "TestFans",
    }
    
    message = THREADS_TEMPLATE.format(**test_data)
    
    print("=" * 50)
    print("THREADS MESSAGE PREVIEW:")
    print("=" * 50)
    print(message)
    print("=" * 50)
    print(f"\nCharacter count: {len(message)}/500")
    print(f"Newlines detected: {message.count(chr(10))}")
    
    return message

async def send_test_post():
    """Send a test post to Meta Threads to verify configuration."""
    if not THREADS_ACCESS_TOKEN or not THREADS_USER_ID:
        print("\n❌ Error: THREADS_ACCESS_TOKEN or THREADS_USER_ID not found in .env")
        return False
        
    test_message = "[TEST] Test message from bot!\n\nLine 2 here\nLine 3 here\n\n✅ If you see this on Threads, it works!"
    
    print("\n🧵 Sending test post to Meta Threads...")
    print("-" * 50)
    print(test_message)
    print("-" * 50)
    
    success = await post_threads_meta(test_message)
    
    if success:
        print("\n✅ Threads post successful!")
    else:
        print("\n❌ Threads post failed. Check the logs above for details.")
    
    return success

async def main():
    print("\n🧵 Meta Threads Message Test Script\n")
    
    # Check if configured
    if not THREADS_ACCESS_TOKEN or not THREADS_USER_ID:
        print("⚠️ Warning: Meta Threads credentials are not fully configured in .env")
        print("You can still preview the message, but sending will fail.\n")
    
    # First preview the template
    preview_message()
    
    # Ask if user wants to send a test post
    print("\n" + "=" * 50)
    choice = input("\nSend a test post to Meta Threads? (y/n): ").strip().lower()
    
    if choice == 'y':
        await send_test_post()
    else:
        print("👍 Preview only - no post sent.")

if __name__ == "__main__":
    asyncio.run(main())
