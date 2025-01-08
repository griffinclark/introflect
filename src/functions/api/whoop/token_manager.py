import threading
from src.utils.firebase.firestore.user_secrets_manager import crud_user_secret
import requests
import time


class WhoopTokenManager:
    def __init__(self, uid, client_id, client_secret, redirect_uri, token_url):
        self.uid = uid
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.token_url = token_url
        self.lock = threading.Lock()
        self.cached_access_token = None
        self.token_expiry = 0  # Unix timestamp

    def _refresh_access_token(self):
        refresh_token = crud_user_secret(self.uid, "whoop", "read")
        if not refresh_token:
            raise ValueError("No refresh token found for the user.")

        # print(f"Refreshing access token for UID: {self.uid}")
        request_data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
        }

        response = requests.post(self.token_url, data=request_data)
        response.raise_for_status()

        tokens = response.json()
        new_access_token = tokens.get("access_token")
        new_refresh_token = tokens.get("refresh_token")
        expires_in = tokens.get("expires_in", 3600)

        if not new_access_token:
            raise ValueError("No access token received from WHOOP API.")

        # Update cached token and expiry
        self.cached_access_token = new_access_token
        self.token_expiry = time.time() + expires_in - 60  # Add buffer for expiration

        # Update refresh token if provided
        if new_refresh_token:
            crud_user_secret(self.uid, "whoop", "update", value=new_refresh_token)

        # print(f"Access token refreshed for UID: {self.uid}")
        return self.cached_access_token

    def get_access_token(self):
        with self.lock:
            if time.time() < self.token_expiry and self.cached_access_token:
                # print("Returning cached access token.")
                return self.cached_access_token

            # print("Cached token expired or missing. Refreshing token.")
            return self._refresh_access_token()
