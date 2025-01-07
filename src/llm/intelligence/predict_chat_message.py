import os
import json
from typing import List, Dict, Any
from dotenv import load_dotenv
import anthropic
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from concurrent.futures import ThreadPoolExecutor
from src.functions.api.ezchecklist.ezchecklist_data_handler import get_ezchecklist_data_for_days
from src.functions.api.whoop.whoop_data_fetcher import WhoopDataFetcher
from src.functions.api.notion.notion_data_handler import get_entries_with_content_for_n_days
from src.functions.api.whoop.token_manager import WhoopTokenManager

# Load environment variables from a .env file
load_dotenv()

# Get the Anthropic API key from environment variables
API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not API_KEY:
    raise ValueError("Anthropic API key is missing. Please set your API key in a .env file.")

os.environ["ANTHROPIC_API_KEY"] = API_KEY

# Initialize the Anthropic chat model
model = ChatAnthropic(
    model="claude-3-5-sonnet-20241022",  # Specify the desired model version
    temperature=0.7,                     # Adjust the temperature for response variability
    max_tokens=1024                      # Set a valid maximum output length
)

# Load tools JSON
with open("./src/llm/context/tools/input_tools.json", "r") as f:
    tools = json.load(f)

# Define ToolResponse type
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
def execute_tool(tool_name: str, params: Dict[str, Any]) -> ToolResponse:
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

            output = whoop_fetcher.fetch_whoop_data(data_type, num_days)
        elif tool_name == "EZChecklist Data":
            num_days = params.get("num_days", 7)
            output = get_ezchecklist_data_for_days(num_days)
        elif tool_name == "Morning Journaling Exercises":
            num_days = params.get("num_days", 7)
            output = get_entries_with_content_for_n_days(num_days)
        else:
            output = f"Unknown tool: {tool_name}"

        return ToolResponse(tool_name=tool_name, params=params, output=output)
    except Exception as e:
        return ToolResponse(tool_name=tool_name, params=params, output=f"Error: {str(e)}")
def query_user(question: str) -> str:
    """Prompt the user for an answer to a given question."""
    print(f"Query: {question}")
    return input("Your response: ")

# Determine relevant tools using LLM
def determine_tools_with_llm(user_query: str) -> List[Dict[str, Any]]:
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

IMPORTANT: Only output the JSON array. Do not include any extra text, prefix, suffix, or characters outside of the JSON array as it will break the system.
"""
    message = HumanMessage(content=tools_prompt)
    response = model.invoke([message])

    # Log the raw response for debugging
    print("Raw LLM Response:", response.content)

    if not response.content.strip():
        print("Error: LLM returned an empty response for tool selection.")
        return []

    try:
        return json.loads(response.content)
    except json.JSONDecodeError as e:
        print(f"Error parsing LLM response as JSON: {e}")
        print("Response content:", response.content)
        return []

# Execute tools in parallel
def execute_tools(tools_to_use: List[Dict[str, Any]]) -> List[ToolResponse]:
    results = []
    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(execute_tool, tool["tool_name"], tool["params"]): tool["tool_name"] for tool in tools_to_use}
        for future in futures:
            tool_name = futures[future]
            try:
                results.append(future.result())
            except Exception as e:
                results.append(ToolResponse(tool_name=tool_name, params={}, output=f"Error: {str(e)}"))
    return results

# Generate a response from the LLM
def generate_response_with_data(user_query: str, tool_outputs: List[ToolResponse]):
    combined_data = "\n".join([f"{tool.tool_name}: {tool.output}" for tool in tool_outputs])
    prompt = f"User Query: {user_query}\nCombined Data:\n{combined_data}\n\nGenerate an answer based on the above data."
    message = HumanMessage(content=prompt)
    response = model.invoke([message])
    return response.content

# Main CLI loop
def main():
    print("Welcome to the LangChain Anthropic CLI Chat!")
    print("Type 'exit' to end the session.")

    while True:
        user_input = input("You: ")
        if user_input.lower() == 'exit':
            print("Ending the chat session. Goodbye!")
            break

        # Step 1: Determine tools using LLM
        tool_selection = determine_tools_with_llm(user_input)
        if not tool_selection:
            print("No tools selected. Please try a different query.")
            continue

        print("Tool Selection:")
        print(json.dumps(tool_selection, indent=2))

        # Step 2: Execute tools and gather data
        tool_outputs = execute_tools(tool_selection)

        # Step 3: Generate response with data
        final_response = generate_response_with_data(user_input, tool_outputs)
        print(f"Claude: {final_response}")

if __name__ == "__main__":
    main()