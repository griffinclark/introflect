import os
import requests
from datetime import datetime, timedelta, timezone
from whoop_auth_handler import get_whoop_access_token

# Constants
BASE_URL = "https://api.prod.whoop.com/developer/v1"
RECOVERY_ENDPOINT = f"{BASE_URL}/recovery"
WORKOUT_COLLECTION=f"{BASE_URL}/activity/workout"
SLEEP_COLLECTION=f"{BASE_URL}/activity/sleep"
CYCLE_COLLECTION=f"{BASE_URL}/cycle"

def fetch_last_14_days_workouts():
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

    all_workouts = []
    next_token = None

    while True:
        if next_token:
            params["nextToken"] = next_token

        response = requests.get(CYCLE_COLLECTION, headers=headers, params=params)
        if response.status_code == 401:
            print("Unauthorized request. Check your access token or scopes.")
            print("Response Content:", response.text)
            return []

        response.raise_for_status()
        data = response.json()
        all_workouts.extend(data.get("records", []))

        next_token = data.get("next_token")
        if not next_token:
            break

    return all_workouts

if __name__ == "__main__":
    try:
        workouts = fetch_last_14_days_workouts()
        print("Fetched Workouts:", workouts)
    except Exception as e:
        print(f"An error occurred: {e}")
