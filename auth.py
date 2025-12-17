import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# If modifying these scopes, delete the file token.json.
SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/spreadsheets'
]

def authenticate_google_apis():
    """
    Handles the OAuth 2.0 flow to authenticate the user.
    Returns:
        creds: The authenticated Google credentials object.
    """
    creds = None
    
    # 1. Check if we already have a valid token (saved from a previous login)
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # 2. If no valid credentials, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # Refresh the token if it's just expired
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Error refreshing token: {e}")
                creds = None # Force re-login

        if not creds:
            # Start the standard "Login with Google" browser flow
            if not os.path.exists('credentials.json'):
                raise FileNotFoundError("Could not find credentials.json. Did you download it from Google Cloud Console?")
            
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        # 3. Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
            
    return creds

if __name__ == '__main__':
    # Test the auth flow immediately when running this file directly
    print("Attempting to authenticate...")
    try:
        credentials = authenticate_google_apis()
        print("SUCCESS! Authentication complete.")
        print(f"Token saved to: {os.path.abspath('token.json')}")
    except Exception as e:
        print(f"FAILED: {e}")