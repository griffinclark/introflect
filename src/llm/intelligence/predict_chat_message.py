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

# Generate a response from the LLM
def generate_response_with_data(user_query: str, tool_outputs: List[Any]):
    combined_data = "\n".join([json.dumps(tool, indent=2) for tool in tool_outputs])
    second_llm_prompt = f"You are a friendly professional psychologist. Speak as a human would, focusing on responding conversationally. Continue this chat. Shoot for an output length of 2-5 sentences. User Query: {user_query}\nCombined Data:\n{combined_data}\n\nGenerate an answer based on the above data."
    message = HumanMessage(content=second_llm_prompt)
    second_llm_response = model.invoke([message])  # Use invoke instead of __call__
    return second_llm_response.content, second_llm_prompt

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
        first_llm_response = select_input_tools_with_llm(user_input)

        # Try parsing the LLM response
        tools_to_use = None
        try:
            tools_to_use = json.loads(first_llm_response)
        except json.JSONDecodeError as e:
            print(f"Error parsing LLM response as JSON: {e}")
            print("LLM Response (raw):", first_llm_response)
            print("Please try a different query.")
            continue  # Allow the user to input another query

        if not tools_to_use:
            print("No tools determined from the LLM response. No additional context will be provided")
            continue

        # Step 2: Execute tools and gather data
        try:
            tool_outputs = [execute_tool(tool["tool_name"], tool["params"]) for tool in tools_to_use]
        except Exception as e:
            print(f"Error executing tools: {e}")
            continue

        # Step 3: Generate response with data
        second_llm_response, second_llm_prompt = generate_response_with_data(user_input, tool_outputs)

        print("Claude: ", second_llm_response)

if __name__ == "__main__":
    main()
