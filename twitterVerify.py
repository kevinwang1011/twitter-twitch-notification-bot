import tweepy

# These come from your Developer Portal (main account creates the app)
API_KEY = "6qxJ1W5xXLnkO6LECva5b2kaw"
API_SECRET = "7TEoTsinprJ2eIJkiU54EHopoewNvrZz9PLlNsyOpvVQMxrCBe"

def authorize_bot_account():
    """
    Run this ONCE to authorize your bot account.
    This will give you Access Token and Access Token Secret for your bot.
    """
    auth = tweepy.OAuthHandler(API_KEY, API_SECRET)
    
    try:
        # Get authorization URL
        redirect_url = auth.get_authorization_url()
        print("\n" + "="*60)
        print("AUTHORIZATION STEPS:")
        print("="*60)
        print("\n1. LOG OUT of Twitter in your browser")
        print("2. LOG IN with your BOT account")
        print("3. Open this URL in your browser:\n")
        print(redirect_url)
        print("\n4. Authorize the app")
        print("5. Copy the PIN/verifier code you receive")
        print("="*60 + "\n")
        
        # Get the verifier code from user
        verifier = input("Enter the PIN/verifier code: ").strip()
        
        # Get access token
        auth.get_access_token(verifier)
        
        print("\n" + "="*60)
        print("SUCCESS! Save these credentials:")
        print("="*60)
        print(f"\nACCESS_TOKEN = \"{auth.access_token}\"")
        print(f"ACCESS_TOKEN_SECRET = \"{auth.access_token_secret}\"")
        print("\n" + "="*60)
        print("\nAdd these to your bot code or .env file!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"Error during authorization: {e}")

if __name__ == "__main__":
    print("\n🤖 Twitter Bot Account Authorization")
    print("This script will help you authorize your bot account.\n")
    authorize_bot_account()