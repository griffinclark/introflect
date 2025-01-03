import os
import secrets
import requests
from dotenv import load_dotenv
from urllib.parse import urlencode, urlparse, parse_qs
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
from src.resources.firebase.firebase_init import firestore_client

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
AUTH_CODE = None  # To store the authorization code dynamically

# Save refresh token to Firestore
def save_refresh_token(refresh_token):
    firestore_client.collection(FIRESTORE_COLLECTION).document(FIRESTORE_DOCUMENT).set(
        {"refresh_token": refresh_token}, merge=True
    )

# Fetch refresh token from Firestore
def get_refresh_token():
    doc = firestore_client.collection(FIRESTORE_COLLECTION).document(FIRESTORE_DOCUMENT).get()
    if not doc.exists:
        raise ValueError("Refresh token not found in Firestore. Please authorize the application.")
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
    save_refresh_token(tokens.get("refresh_token", ""))
    return tokens["access_token"]

# Refresh access token
def refresh_access_token():
    refresh_token = get_refresh_token()
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
    save_refresh_token(tokens.get("refresh_token", ""))
    return tokens["access_token"]

# Validate access token
def validate_access_token(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(DATA_ENDPOINT, headers=headers)
    if response.status_code == 401:
        raise ValueError("Access token is invalid or expired.")
    response.raise_for_status()
    print("Access token validated successfully.")

# Generate the authorization URL
def generate_auth_url():
    scopes = [
        "offline",
        "read:workout",
        "read:cycles",
        "read:sleep",
        "read:recovery",
        "read:profile",
        "read:body_measurement"
    ]
    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": " ".join(scopes),
        "state": STATE
    }
    return f"{AUTH_URL}?{urlencode(params)}"


# OAuth server to handle callback
class OAuthCallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global AUTH_CODE
        parsed_url = urlparse(self.path)
        if parsed_url.path == '/callback':
            query_components = parse_qs(parsed_url.query)
            if query_components.get('state', [None])[0] != STATE:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"State parameter mismatch.")
                return
            AUTH_CODE = query_components.get('code', [None])[0]
            if AUTH_CODE:
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"Authorization code received. You can close this window.")
            else:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Missing authorization code.")
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found.")

def run_server():
    server_address = ('', 8642)
    httpd = HTTPServer(server_address, OAuthCallbackHandler)
    thread = threading.Thread(target=httpd.serve_forever)
    thread.daemon = True
    thread.start()
    return httpd

# Get WHOOP access token
def get_whoop_access_token():
    global AUTH_CODE
    try:
        refresh_token = get_refresh_token()
        return refresh_access_token()
    except ValueError:
        print("Starting server to handle authorization callback...")
        server = run_server()
        print("Authorization URL:", generate_auth_url())
        input("Press Enter after authorizing the app...")
        server.shutdown()
        if not AUTH_CODE:
            raise ValueError("Authorization code was not received.")
        return exchange_auth_code_for_tokens(AUTH_CODE)

if __name__ == "__main__":
    try:
        access_token = get_whoop_access_token()
        validate_access_token(access_token)
        print("Access Token:", access_token)
    except Exception as e:
        print(f"An error occurred: {e}")
