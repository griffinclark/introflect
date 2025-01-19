# tool_handler.py
import os
import json
from typing import Dict, Any, List
from src.functions.api.ezchecklist.ezchecklist_data_handler import get_ezchecklist_data_for_days
from src.functions.api.whoop.token_manager import WhoopTokenManager
from src.functions.api.whoop.whoop_data_fetcher import WhoopDataFetcher
from src.functions.api.notion.notion_data_handler import get_entries_with_content_for_n_days
from src.interface.output_manager import OutputManager  # Add this import
from src.utils.firebase.firebase_init import firestore_client
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage

class ToolResponse:
    def __init__(self, tool_name: str, params: Dict[str, Any], output: Any):
        self.tool_name = tool_name
        self.params = params
        self.output = output

    def to_dict(self) -> Dict[str, Any]:
        """Convert ToolResponse to a dictionary for JSON serialization."""
        return {
            "tool_name": self.tool_name,
            "params": self.params,
            "output": self.output
        }

# Real implementations of tool functions

def execute_tools(raw_tool_choices: str, output_manager: OutputManager) -> List[ToolResponse]:
    """
    Executes a list of tools with their respective parameters, taking in raw JSON input.

    Args:
        raw_tool_choices (str): A JSON string containing the tool choices with parameters.

    Returns:
        List[ToolResponse]: A list of ToolResponse objects with tool outputs.
    """
    try:
        # Parse the raw JSON string into a list of dictionaries
        tools = json.loads(raw_tool_choices)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse tool choices: {e}")

    results = []
    for tool in tools:
        tool_name = tool.get("tool_name")
        params = tool.get("params", {})
        try:
            output = execute_tool(tool_name, params)
            tool_response = ToolResponse(tool_name=tool_name, params=params, output=output)
            output_manager.log(f"    ✅ Executed tool: {tool_name}")
            results.append(tool_response)
        except Exception as e:
            tool_response = ToolResponse(tool_name=tool_name, params=params, output=f"Error: {str(e)}")
            results.append(tool_response)
    return results

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
        elif tool_name == "Read Personality Profile":
            # get the user's personality profile from Firestore
            doc_ref = firestore_client.collection(
                "personality_profiles").document("g")  # TODO this is hardcoded
            doc = doc_ref.get()
            if doc.exists:
                return doc.to_dict()["metrics"]
            else:
                return "No personality profile found."

        else:
            return f"Unknown tool: {tool_name}"
    except Exception as e:
        return f"Error: {str(e)}"


# Determine relevant tools using LLM
def select_input_tools_with_llm(user_query: str) -> str:

    API_KEY = os.getenv("ANTHROPIC_API_KEY")
    if not API_KEY:
        raise ValueError(
            "Anthropic API key is missing. Please set your API key in a .env file.")

    # Initialize the Anthropic chat model
    model = ChatAnthropic(
        model="claude-3-5-sonnet-20241022",  # Specify model version
        temperature=0.4,                     # Adjust temperature for response variability
        anthropic_api_key=API_KEY            # Use the API key
    )

    # Load tools JSON
    with open("./src/llm/context/tools/input_tools.json", "r") as f:
        tools = json.load(f)

    tools_prompt = f"""
Available Tools:

{json.dumps(tools, indent=2)}

User Query:
{user_query}

Determine which tools to use and provide parameters for each tool. Output a JSON array in the following format:
[
  {{
    "tool_name": "<tool_name>",
    "params": {{"<param1>": <value1>, "<param2>": <value2>}}
  }}
]

STRICTLY return only the JSON array. Any additional text will cause an error. I will give you a $100 tip if you follow these instructions perfectly, and only return structured JSON that works with my code.

Your response must properly load with this code: tools_to_use = json.loads(llm_response)
"""
    message = HumanMessage(content=tools_prompt)
    response = model.invoke([message])
    return response.content
