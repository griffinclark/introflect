# tool_handler.py
import os
import json
from typing import Dict, Any
from src.functions.api.ezchecklist.ezchecklist_data_handler import get_ezchecklist_data_for_days
from src.functions.api.whoop.token_manager import WhoopTokenManager
from src.functions.api.whoop.whoop_data_fetcher import WhoopDataFetcher
from src.functions.api.notion.notion_data_handler import get_entries_with_content_for_n_days
from src.utils.firebase.firebase_init import firestore_client

class ToolResponse:
    def __init__(self, tool_name: str, params: Dict[str, Any], output: Any):
        self.tool_name = tool_name
        self.params = params
        self.output = output

    def to_dict(self):
        return {
            "tool_name": self.tool_name,
            "params": self.params,
            "output": self.output
        }

# Real implementations of tool functions
def execute_tool(tool_name: str, params: Dict[str, Any]) -> str:
    try:
        if tool_name.startswith("WHOOP Data"):
            data_type = tool_name.split(" - ")[1].lower()
            num_days = params.get("num_days", 7)

            # Initialize TokenManager and WhoopDataFetcher
            token_manager = WhoopTokenManager(
                uid="g",
                client_id=os.getenv("WHOOP_CLIENT_ID"),
                client_secret=os.getenv("WHOOP_CLIENT_SECRET"),
                redirect_uri="http://localhost:8642/callback",
                token_url="https://api.prod.whoop.com/oauth/oauth2/token",
            )
            whoop_fetcher = WhoopDataFetcher(token_manager)

            return whoop_fetcher.fetch_whoop_data(data_type, num_days)
        elif tool_name == "EZChecklist Data":
            num_days = params.get("num_days", 7)
            return get_ezchecklist_data_for_days(num_days)
        elif tool_name == "Morning Journaling Exercises":
            num_days = params.get("num_days", 7)
            return get_entries_with_content_for_n_days(num_days)
        elif tool_name =="Read Personality Profile":
            # get the user's personality profile from Firestore
            doc_ref = firestore_client.collection("personality_profiles").document("g") #TODO this is hardcoded
            doc = doc_ref.get()
            if doc.exists:
                return doc.to_dict()["metrics"]
            else:
                return "No personality profile found."

        else:
            return f"Unknown tool: {tool_name}"
    except Exception as e:
        return f"Error: {str(e)}"