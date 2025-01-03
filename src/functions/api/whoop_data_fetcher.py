import os
import requests
from datetime import datetime, timedelta, timezone
from whoop_auth_handler import get_whoop_access_token
from enum import Enum


class WhoopDataType(Enum):
    RECOVERY = "recovery"
    WORKOUT = "activity/workout"
    SLEEP = "activity/sleep"
    CYCLE = "cycle"


# Constants
BASE_URL = "https://api.prod.whoop.com/developer/v1"
ENDPOINTS = {
    "recovery": f"{BASE_URL}/recovery",
    "workout": f"{BASE_URL}/activity/workout",
    "sleep": f"{BASE_URL}/activity/sleep",
    "cycle": f"{BASE_URL}/cycle",
}


def fetch_whoop_data(data_type: str, days: int, limit: int = 25):
    """
    Fetches WHOOP data for the specified type and date range.

    Args:
        data_type (str): The type of data to fetch ("recovery", "workout", "sleep", "cycle").
        days (int): The number of days in the past to fetch data for.
        limit (int): The maximum number of records per request (default: 25).

    Returns:
        list: A list of fetched data records.
    """
    if data_type not in ENDPOINTS:
        raise ValueError(f"Invalid data type '{data_type}'. Must be one of {list(ENDPOINTS.keys())}.")

    # Get the access token
    access_token = get_whoop_access_token()
    headers = {"Authorization": f"Bearer {access_token}"}

    # Calculate date range
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)

    # Convert dates to ISO format
    start_date_str = start_date.isoformat()
    end_date_str = end_date.isoformat()

    # Initialize parameters
    params = {
        "start": start_date_str,
        "end": end_date_str,
        "limit": limit,
    }

    all_data = []
    next_token = None

    while True:
        if next_token:
            params["nextToken"] = next_token

        response = requests.get(ENDPOINTS[data_type], headers=headers, params=params)
        if response.status_code == 401:
            print("Unauthorized request. Check your access token or scopes.")
            print("Response Content:", response.text)
            return []

        response.raise_for_status()
        data = response.json()
        all_data.extend(data.get("records", []))

        next_token = data.get("next_token")
        if not next_token:
            break

    return all_data

if __name__ == "__main__":
    try:
        raw_data_types = input(
            "Enter the types of data to fetch (e.g., recovery, workout, sleep, cycle): ").strip()
        data_types = [dt.strip() for dt in raw_data_types.split(",") if dt.strip()]

        days = int(input("Enter the number of days to fetch data for: ").strip())

        for data_type in data_types:
            if data_type not in ENDPOINTS:
                print(f"Skipping invalid data type: {data_type}")
                continue
            print(f"Fetching {data_type.capitalize()} data...")
            fetched_data = fetch_whoop_data(data_type, days)
            print(f"Fetched {data_type.capitalize()} Data:", fetched_data)

    except Exception as e:
        print(f"An error occurred: {e}")

