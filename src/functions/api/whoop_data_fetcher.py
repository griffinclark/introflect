import os
import requests
from datetime import datetime, timedelta, timezone
from whoop_auth_handler import get_whoop_access_token

# Constants
BASE_URL = "https://api.prod.whoop.com/developer/v1"
CYCLES_ENDPOINT = f"{BASE_URL}/cycle"

# Function to fetch data for the last 14 days
def fetch_last_14_days_data():
    # Get the access token
    access_token = get_whoop_access_token()
    headers = {"Authorization": f"Bearer {access_token}"}

    # Calculate date range
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=14)

    # Convert dates to ISO format
    start_date_str = start_date.isoformat()
    end_date_str = end_date.isoformat()

    # Initialize parameters
    params = {
        "start": start_date_str,
        "end": end_date_str,
        "limit": 25  # Adjust as needed; WHOOP API may have a maximum limit per request
    }

    all_data = []
    while True:
        response = requests.get(CYCLES_ENDPOINT, headers=headers, params=params)
        if response.status_code == 401:
            print("Unauthorized request. Check your access token or scopes.")
            print("Response Content:", response.text)
            return []

        response.raise_for_status()
        data = response.json()
        all_data.extend(data)

        # Check if there's more data to fetch
        if len(data) < params["limit"]:
            break

        # Update the start date for the next batch
        params["start"] = data[-1]["start"]

    return all_data

if __name__ == "__main__":
    try:
        data = fetch_last_14_days_data()
        print("Fetched Data:", data)
    except Exception as e:
        print(f"An error occurred: {e}")
