from datetime import datetime, timedelta, timezone
from src.utils.constants import WHOOPRecovery, WHOOPWorkout, WHOOPSleep, WHOOPCycle
from typing import List, Union
import requests

from src.functions.api.whoop.token_manager import WhoopTokenManager


class WhoopDataFetcher:
    BASE_URL = "https://api.prod.whoop.com/developer/v1"
    ENDPOINTS = {
        "recovery": f"{BASE_URL}/recovery",
        "workout": f"{BASE_URL}/activity/workout",
        "sleep": f"{BASE_URL}/activity/sleep",
        "cycle": f"{BASE_URL}/cycle",
    }

    def __init__(self, token_manager: WhoopTokenManager):
        self.token_manager = token_manager

    def fetch_whoop_data(self, data_type: str, days: int, limit: int = 25):
        if data_type not in self.ENDPOINTS:
            raise ValueError(f"Invalid data type '{data_type}'. Must be one of {list(self.ENDPOINTS.keys())}.")

        access_token = self.token_manager.get_access_token()
        headers = {"Authorization": f"Bearer {access_token}"}

        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        params = {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "limit": limit,
        }

        all_data = []
        next_token = None

        while True:
            if next_token:
                params["nextToken"] = next_token

            response = requests.get(self.ENDPOINTS[data_type], headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

            all_data.extend(data.get("records", []))
            next_token = data.get("next_token")
            if not next_token:
                break

        return all_data
