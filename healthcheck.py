import os
import sys
import requests

def check_bot_health():
    try:
        # Get token from environment variable instead of file
        token = os.getenv('BOT_TOKEN')
        if not token:
            print("BOT_TOKEN environment variable not found")
            sys.exit(1)

        # Make request to Telegram API
        response = requests.get(f'https://api.telegram.org/bot{token}/getMe')
        
        # Print response for debugging
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        # Exit with appropriate code
        sys.exit(0 if response.status_code == 200 else 1)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    check_bot_health()
