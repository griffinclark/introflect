import os
import json
from dotenv import load_dotenv
from typing import List, Any
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from src.llm.context.tools.tool_handler import execute_tools, select_input_tools_with_llm

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
        raw_tool_choices = select_input_tools_with_llm(user_query)  # Get raw JSON
    except Exception as e:
        raise RuntimeError(f"Error selecting tools: {e}")

    # Step 2: Execute tools and gather data
    try:
        tool_outputs = execute_tools(raw_tool_choices)  # Pass raw JSON to execute_tools
    except Exception as e:
        raise RuntimeError(f"Error executing tools: {e}")

    # Step 3: Generate response with data
    combined_data = "\n".join([json.dumps(tool.to_dict(), indent=2) for tool in tool_outputs])  # Serialize ToolResponse objects
    second_llm_prompt = (
        f"You are a friendly professional. Speak as a human would, focusing on responding conversationally. "
        f"Continue this chat. Shoot for an output length of 2-5 sentences. "
        f"User Query: {user_query}\nCombined Data:\n{combined_data}\n\nGenerate an answer based on the above data."
    )
    try:
        second_llm_response = model.invoke([HumanMessage(content=second_llm_prompt)])
        return second_llm_response.content
    except Exception as e:
        raise RuntimeError(f"Error generating response: {e}")

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
