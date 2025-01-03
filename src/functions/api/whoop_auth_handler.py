import os
import secrets
import requests
from dotenv import load_dotenv
from src.resources.firebase.firebase_init import firestore_client  # Import Firestore client

# Load environment variables from .env
load_dotenv()

# Validate environment variables
CLIENT_ID = os.getenv("WHOOP_CLIENT_ID")
CLIENT_SECRET = os.getenv("WHOOP_CLIENT_SECRET")
REDIRECT_URI = "http://localhost:8642/callback"
if not CLIENT_ID or not CLIENT_SECRET or not REDIRECT_URI:
    print(CLIENT_ID)
    print(CLIENT_SECRET)
    raise ValueError("Missing CLIENT_ID or CLIENT_SECRET in environment variables.")

# Constants
AUTH_URL = "https://api.prod.whoop.com/oauth/oauth2/auth"
TOKEN_URL = "https://api.prod.whoop.com/oauth/oauth2/token"
DATA_ENDPOINT = "https://api.prod.whoop.com/developer/v1/user/profile/basic"
FIRESTORE_COLLECTION = "app_secrets"
FIRESTORE_DOCUMENT = "whoop"

# Secure state generation and validation
STATE = secrets.token_urlsafe(16)

# Save refresh token to Firestore
def save_refresh_token(refresh_token):
    firestore_client.collection(FIRESTORE_COLLECTION).document(FIRESTORE_DOCUMENT).set(
        {"refresh_token": refresh_token}, merge=True
    )

# Fetch refresh token from Firestore
def get_refresh_token():
    doc = firestore_client.collection(FIRESTORE_COLLECTION).document(FIRESTORE_DOCUMENT).get()
    if not doc.exists:
        print("No document found in Firestore. Please initialize the process to get an authorization code.")
        raise ValueError("Refresh token not found in Firestore. You need to authorize the application.")

    refresh_token = doc.to_dict().get("refresh_token")
    if not refresh_token:
        raise ValueError("Refresh token is missing in Firestore.")

    return refresh_token

# Exchange authorization code for tokens
def exchange_auth_code_for_tokens(auth_code):
    print("Exchanging authorization code for tokens...")
    response = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": auth_code,
            "redirect_uri": REDIRECT_URI,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        },
    )
    response.raise_for_status()
    tokens = response.json()
    print("Tokens received:", tokens)

    # Save refresh token
    if "refresh_token" not in tokens:
        raise ValueError("WHOOP API did not return a refresh token.")
    save_refresh_token(tokens["refresh_token"])
    return tokens["access_token"]

# Refresh access token
def refresh_access_token():
    refresh_token = get_refresh_token()
    print("Refreshing access token using refresh token...")
    response = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        },
    )
    response.raise_for_status()
    tokens = response.json()

    # Update refresh token if it changes
    if "refresh_token" in tokens:
        save_refresh_token(tokens["refresh_token"])

    return tokens["access_token"]

# Fetch WHOOP data
def fetch_whoop_data(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(DATA_ENDPOINT, headers=headers)
    response.raise_for_status()
    return response.json()

# Generate the authorization URL
def generate_auth_url():
    scopes = "offline%20read:profile%20read:cycles"
    return (
        f"{AUTH_URL}?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}"
        f"&scope={scopes}&state={STATE}"
    )

def validate_access_token(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(DATA_ENDPOINT, headers=headers)
    if response.status_code == 401:
        raise ValueError("Access token is invalid or expired. Please reauthorize.")
    response.raise_for_status()
    print("Access token validated successfully.")

def get_whoop_access_token():
    access_token = None
    try:
        refresh_token = get_refresh_token()
        print("Refresh token found. Using refresh token to get access token.")
        access_token = refresh_access_token()
    except ValueError:
        # No refresh token found
        print("No refresh token found. Starting authorization code flow.")
        print("Generate an authorization URL and paste it into your browser:")
        print(generate_auth_url())
        auth_code = input("Enter the authorization code from WHOOP: ").strip()
        access_token = exchange_auth_code_for_tokens(auth_code)

    # Validate the access token
    validate_access_token(access_token)
    return access_token

def main():
    print("=== WHOOP API Token Fetcher ===")
    try:
        # Check if refresh token exists
        try:
            refresh_token = get_refresh_token()
            print("Refresh token found. Using refresh token to get access token.")
            access_token = refresh_access_token()
        except ValueError:
            # No refresh token found
            print("No refresh token found. Starting authorization code flow.")
            print("Generate an authorization URL and paste it into your browser:")
            print(generate_auth_url())

            # Ask for the authorization code
            auth_code = input("Enter the authorization code from WHOOP: ").strip()

            # Exchange authorization code for tokens
            access_token = exchange_auth_code_for_tokens(auth_code)

        # Fetch WHOOP data
        print("Fetching WHOOP data...")
        data = fetch_whoop_data(access_token)
        print("WHOOP Data:", data)
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
