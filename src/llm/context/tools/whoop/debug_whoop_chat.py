import os
import secrets
import requests
from dotenv import load_dotenv
from urllib.parse import urlencode, urlparse, parse_qs
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
from src.utils.firebase.firestore.user_manager import crud_user_secret

# Load environment variables from .env
load_dotenv()

# Validate environment variables
CLIENT_ID = os.getenv("WHOOP_CLIENT_ID")
CLIENT_SECRET = os.getenv("WHOOP_CLIENT_SECRET")
REDIRECT_URI = "http://localhost:8642/callback"
if not CLIENT_ID or not CLIENT_SECRET or not REDIRECT_URI:
    raise ValueError("Missing CLIENT_ID, CLIENT_SECRET, or REDIRECT_URI in environment variables.")

# Constants
AUTH_URL = "https://api.prod.whoop.com/oauth/oauth2/auth"
TOKEN_URL = "https://api.prod.whoop.com/oauth/oauth2/token"
DATA_ENDPOINT = "https://api.prod.whoop.com/developer/v1/user/profile/basic"

# Secure state generation and validation
STATE = secrets.token_urlsafe(16)
AUTH_CODE = None  # To store the authorization code dynamically

def debug_log(stage, details):
    """Utility function to print detailed debugging information."""
    print(f"[DEBUG] Stage: {stage}")
    for key, value in details.items():
        print(f"  {key}: {value}")

# Exchange authorization code for tokens
def exchange_auth_code_for_tokens(uid, auth_code):
    debug_log("Exchange Auth Code", {"uid": uid, "auth_code": auth_code})
    try:
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
        debug_log("Token Exchange Response", {"status_code": response.status_code, "response_text": response.text})
        response.raise_for_status()
        tokens = response.json()

        # Save the refresh token immediately
        refresh_token = tokens.get("refresh_token")
        if not refresh_token:
            raise ValueError("No refresh token received from WHOOP API.")
        crud_user_secret(uid, "whoop", "create", value=refresh_token)
        return tokens["access_token"]
    except requests.exceptions.RequestException as e:
        debug_log("Exchange Auth Code Error", {"error": str(e), "response_text": e.response.text if e.response else "No response content"})
        raise

# Refresh access token
def refresh_access_token(uid):
    try:
        refresh_token = crud_user_secret(uid, "whoop", "read")
        if not refresh_token:
            raise ValueError("No refresh token found for the user.")

        debug_log("Refresh Token Retrieved", {"uid": uid, "refresh_token": refresh_token})
        
        # Refresh token request
        request_data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI,  # Explicitly include redirect_uri if required
        }
        debug_log("Refresh Token Request Data", request_data)
        
        # Send request
        response = requests.post(TOKEN_URL, data=request_data)
        
        # Log response
        debug_log("Refresh Token Response", {
            "status_code": response.status_code,
            "response_text": response.text,
        })

        response.raise_for_status()  # Raise an error for non-2xx status codes

        # Parse tokens
        tokens = response.json()
        debug_log("Parsed Token Response", tokens)

        # Save new refresh token
        new_refresh_token = tokens.get("refresh_token")
        if new_refresh_token:
            crud_user_secret(uid, "whoop", "update", value=new_refresh_token)

        return tokens["access_token"]

    except requests.exceptions.RequestException as e:
        debug_log("Refresh Token Request Exception", {
            "error": str(e),
            "response_content": e.response.text if e.response else "No response content",
        })
        raise

    except ValueError as e:
        debug_log("Refresh Token ValueError", {"error": str(e)})
        raise


# Validate access token
def validate_access_token(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    debug_log("Validate Access Token", {"access_token": access_token})
    try:
        response = requests.get(DATA_ENDPOINT, headers=headers)
        debug_log("Access Token Validation Response", {"status_code": response.status_code, "response_text": response.text})
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        debug_log("Access Token Validation Failed", {"error": str(e), "response_text": e.response.text if e.response else "No response content"})
        raise

# Generate the authorization URL
def generate_auth_url():
    scopes = [
        "offline",
        "read:workout",
        "read:cycles",
        "read:sleep",
        "read:recovery",
        "read:profile",
        "read:body_measurement",
    ]
    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": " ".join(scopes),
        "state": STATE,
    }
    url = f"{AUTH_URL}?{urlencode(params)}"
    debug_log("Generate Auth URL", {"url": url})
    return url

# OAuth server to handle callback
class OAuthCallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global AUTH_CODE
        parsed_url = urlparse(self.path)
        if parsed_url.path == "/callback":
            query_components = parse_qs(parsed_url.query)
            debug_log("OAuth Callback", {"query_components": query_components})
            if query_components.get("state", [None])[0] != STATE:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"State parameter mismatch.")
                return
            AUTH_CODE = query_components.get("code", [None])[0]
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
    server_address = ("", 8642)
    httpd = HTTPServer(server_address, OAuthCallbackHandler)
    thread = threading.Thread(target=httpd.serve_forever)
    thread.daemon = True
    thread.start()
    return httpd

# Get WHOOP access token
def get_whoop_access_token(uid):
    global AUTH_CODE
    try:
        refresh_token = crud_user_secret(uid, "whoop", "read")
        debug_log("Get WHOOP Access Token - Refresh Token", {"refresh_token": refresh_token})
        return refresh_access_token(uid)
    except ValueError:
        debug_log("Get WHOOP Access Token - Initiating OAuth Flow", {})
        server = run_server()
        print("Authorization URL:", generate_auth_url())
        input("Press Enter after authorizing the app...")
        server.shutdown()
        if not AUTH_CODE:
            raise ValueError("Authorization code was not received.")
        return exchange_auth_code_for_tokens(uid, AUTH_CODE)

if __name__ == "__main__":
    try:
        uid = input("Enter the UID of the user: ").strip()
        access_token = get_whoop_access_token(uid)
        validate_access_token(access_token)
        print("Access Token:", access_token)
    except Exception as e:
        debug_log("Main Error", {"error": str(e)})
