import os
import json
from dotenv import load_dotenv
from typing import List, Any
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from src.llm.context.tools.tool_handler import execute_tool, select_input_tools_with_llm

# Load environment variables from a .env file
load_dotenv()

# Get the Anthropic API key from environment variables
API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not API_KEY:
    raise ValueError("Anthropic API key is missing. Please set your API key in a .env file.")

# Initialize the Anthropic chat model
model = ChatAnthropic(
    model="claude-3-5-sonnet-20241022",  # Specify model version
    temperature=0.7,                     # Adjust temperature for response variability
    anthropic_api_key=API_KEY            # Use the API key
)

def augmented_chat(user_query: str) -> str:
    """
    Executes the two-step chain:
    1. Uses the LLM to determine tools.
    2. Executes tools and uses the LLM again to generate the final response.

    Args:
        user_query (str): The user's input query.

    Returns:
        str: The LLM's final response.
    """
    # Step 1: Determine tools using LLM
    try:
        first_llm_response = select_input_tools_with_llm(user_query)
        tools_to_use = json.loads(first_llm_response)
    except json.JSONDecodeError as e:
        raise ValueError(f"Error parsing LLM response as JSON: {e}\nRaw Response: {first_llm_response}")
    
    if not tools_to_use:
        return "No tools determined from the LLM response. Unable to proceed."

    # Step 2: Execute tools and gather data
    try:
        tool_outputs = [execute_tool(tool["tool_name"], tool["params"]) for tool in tools_to_use]
    except Exception as e:
        raise RuntimeError(f"Error executing tools: {e}")

    # Step 3: Generate response with data
    combined_data = "\n".join([json.dumps(tool, indent=2) for tool in tool_outputs])
    second_llm_prompt = (
        f"You are a friendly professional psychologist. Speak as a human would, focusing on responding conversationally. "
        f"Continue this chat. Shoot for an output length of 2-5 sentences. "
        f"User Query: {user_query}\nCombined Data:\n{combined_data}\n\nGenerate an answer based on the above data."
    )
    second_llm_response = model.invoke([HumanMessage(content=second_llm_prompt)])
    return second_llm_response.content

# CLI Main Loop
def main():
    print("Welcome to the LangChain Anthropic CLI Chat!")
    print("Type 'exit' to end the session.")

    while True:
        user_input = input("You: ")
        if user_input.lower() == 'exit':
            print("Ending the chat session. Goodbye!")
            break

        try:
            # Call the augmented_chat function
            response = augmented_chat(user_input)
            print("Claude:", response)
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
