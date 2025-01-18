import json
from src.functions.chat.sliding_context_manager import SlidingContextWindow
from src.functions.chat.augmented_chat import augmented_chat

class ChatApplication:
    def __init__(self, max_context_tokens: int = 1000):
        """
        Initializes the ChatApplication with a sliding context window.

        Args:
            max_context_tokens (int): Maximum number of tokens for the context window.
        """
        self.context_manager = SlidingContextWindow(max_context_tokens)

    def add_message_to_context(self, role: str, content: str):
        """
        Adds a message to the sliding context.

        Args:
            role (str): Role of the message (e.g., 'user', 'assistant', 'system').
            content (str): Content of the message.
        """
        self.context_manager.add_message(role, content)

    def get_context(self) -> str:
        """
        Retrieves the serialized context.

        Returns:
            str: The current serialized context as a JSON string.
        """
        return self.context_manager.get_context()

    def chat(self, user_input: str) -> str:
        """
        Manages the chat flow by updating context and invoking the augmented chat.

        Args:
            user_input (str): The user's query.

        Returns:
            str: The assistant's response.
        """
        # Add user input to context
        self.add_message_to_context("user", user_input)

        # Get the current serialized context
        serialized_context = self.get_context()

        # Call the augmented_chat function for a response, passing the context
        response = augmented_chat(user_input, serialized_context)

        # Add assistant response to context
        self.add_message_to_context("assistant", response)

        return response


# CLI Main Loop
def main():
    print("Welcome to the Chat Application!")
    print("Type 'exit' to end the session.")

    chat_app = ChatApplication(max_context_tokens=1000)  # Adjust token limit as needed

    while True:
        user_input = input("You: ")
        if user_input.lower() == 'exit':
            print("Ending the chat session. Goodbye!")
            break

        try:
            # Use the chat application to generate a response
            response = chat_app.chat(user_input)
            print("Assistant:", response)
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
