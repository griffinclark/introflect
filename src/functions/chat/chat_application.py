import json
import datetime
import warnings
from src.functions.chat.augmented_chat import get_augmentation_data
from src.utils.constants import ChatContext, ChatMessage, Conversation, ExpertLLM
from src.utils.firebase.firestore.chat_helper import ChatHelper
from src.llm.intelligence.mixture_of_experts.select_expert import ExpertSelector
from src.interface.output_manager import OutputManager
from langchain_anthropic import ChatAnthropic
import os
from langchain_core.messages import HumanMessage

# Suppress warnings globally
warnings.filterwarnings("ignore")
API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not API_KEY:
    raise ValueError(
        "Anthropic API key is missing. Please set your API key in a .env file.")


class ChatApplication:
    def __init__(self, user_id: str, max_context_tokens: int = 1000, debug: bool = False):
        """
        Initializes the ChatApplication with a ChatContext and ExpertSelector.

        Args:
            user_id (str): Unique identifier for the user.
            max_context_tokens (int): Maximum number of tokens for the context window.
        """
        self.chat_context = ChatContext(
            user_id=user_id, max_tokens=max_context_tokens)
        self.chat_helper = ChatHelper()
        self.expert_selector = ExpertSelector()  # Initialize ExpertSelector
        self.conversation_id = f"conversation_{user_id}_{
            datetime.datetime.now(datetime.timezone.utc).isoformat()}"
        self.chat_context.current_expert = None  # Initialize current expert
        self.output_manager = OutputManager(debug=debug)

        # Attempt to load an existing conversation
        try:
            existing_conversation = self.chat_helper.load_conversation(
                self.conversation_id)
            self.chat_context.context = existing_conversation.messages
            self.chat_context.token_count = sum(
                len(msg.content.split()) for msg in existing_conversation.messages)
            self.chat_context.current_expert = self.expert_selector.select_expert(
                existing_conversation)
        except ValueError:
            self.output_manager.log(
                "No existing conversation found. Starting fresh.", level="INFO")

    def chat(self, user_input: str) -> None:
        """
        Manages the chat flow by updating context and invoking the augmented chat.

        Args:
            user_input (str): The user's query.
        """
        # Add user input to context
        self.add_message_to_context("user", user_input)

        # Determine the expert to use for the response
        conversation = Conversation(
            conversation_id=self.conversation_id,
            user_id=self.chat_context.user_id,
            messages=self.chat_context.context
        )

        # Call select_expert and log its result
        selected_expert, debug_reasoning = self.expert_selector.select_expert(
            conversation,
            current_expert=self.chat_context.current_expert.template_name if self.chat_context.current_expert else None
        )

        if not isinstance(selected_expert, ExpertLLM):
            self.output_manager.log(
                f"Error: select_expert must return an ExpertLLM instance, got {type(selected_expert)}",
                level="ERROR"
            )
            raise ValueError(f"select_expert must return an ExpertLLM instance, got {type(selected_expert)}")

        # Log the reasoning for selecting the expert
        self.output_manager.log(f"🤔 Expert Selection: {selected_expert.template_name}")
        self.output_manager.log(f"🧠 Expert Reasoning: {debug_reasoning}")

        # Update the current expert in the context
        self.chat_context.current_expert = selected_expert

        # Serialize the current context
        serialized_context = self.get_serialized_context()

        # Get the augmentation data
        augmentation_data = get_augmentation_data(
            user_query=user_input, context=serialized_context, output_manager=self.output_manager)

        # Build the prompt template with LangChain
        prompt = f"""
            You are an AI system acting as the expert: {selected_expert.template_name}. Do not talk about yourself or your prompting - just respond in 2-5 sentences (unless you specifically need a longer output)
            Your role is to provide responses based on the following personality traits and instructions:
            - Personality: {selected_expert.personality_prompt}
            - Speaking Style: {selected_expert.speaking_instructions}
            - Tone: {selected_expert.tone}
            - Preferred Response Length: {selected_expert.default_length_preference}
            - Vocabulary Complexity: {selected_expert.preferred_vocabulary_complexity}
            - Specialization Contexts: {selected_expert.when_to_use}

            The user has engaged in the following conversation history:
            {serialized_context}

            Additionally, you have access to the following augmentation data to enhance your response:
            {augmentation_data}

            Now, the user has provided a query:
            User Query: "{user_input}"

            Your task is to:
            1. Provide a detailed and accurate response to the user's query.
            2. Incorporate the augmentation data if it enhances your answer.
            3. Maintain alignment with the expert's personality, tone, and instructions.

            Respond below:
            """

        # Generate response using Claude
        model = ChatAnthropic(
            model="claude-3-5-sonnet-20241022", 
            temperature=selected_expert.temperature or 0.7,
            anthropic_api_key=API_KEY
        )

        message = HumanMessage(content=prompt)
        response = model.invoke([message])

        # Extract content from the response
        response_content = response.content.strip()

        # Log the assistant's response
        self.output_manager.log(f"\n💬 {self.chat_context.current_expert.template_name}: {response_content}")

        # Add assistant response to context
        self.add_message_to_context(
            "assistant",
            response_content,
            expert_used=self.chat_context.current_expert.template_name,
            expert_version=self.chat_context.current_expert.version
        )

    def add_message_to_context(self, role: str, content: str, expert_used: str = "general", expert_version: int = 1):
        """
        Adds a message to the chat context.

        Args:
            role(str): Role of the message(e.g., 'user', 'assistant').
            content(str): Content of the message.
            expert_used(str): Expert template used for the response.
            expert_version(int): Version of the expert used.
        """
        message = ChatMessage(
            role=role,
            content=content,
            expert_used=expert_used,
            expert_version=expert_version,
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        self.chat_context.context.append(message)

        # Update token count
        self.chat_context.token_count += len(content.split())

        # Trim context if token count exceeds max tokens
        self._trim_context()

        # Save the updated conversation to Firestore
        self.chat_helper.save_conversation(
            Conversation(
                conversation_id=self.conversation_id,
                user_id=self.chat_context.user_id,
                messages=self.chat_context.context,
                created_at=self.chat_context.context[0].timestamp if self.chat_context.context else datetime.datetime.now(
                    datetime.timezone.utc)
            )
        )

    def _trim_context(self):
        """
        Trims the chat context to ensure it stays within the token limit.
        """
        while self.chat_context.token_count > self.chat_context.max_tokens:
            removed_message = self.chat_context.context.pop(0)
            self.chat_context.token_count -= len(
                removed_message.content.split())

    def get_serialized_context(self) -> str:
        """
        Retrieves the serialized context.

        Returns:
            str: The current serialized context as a JSON string.
        """
        return json.dumps(
            [{"role": msg.role, "content": msg.content}
                for msg in self.chat_context.context],
            indent=2
        )


# CLI Main Loop
def main():
    print("Welcome to the Chat Application!")
    print("Type 'exit' to end the session.")

    user_id = "g"  # Replace with a dynamic user ID as needed
    # Adjust token limit as needed
    chat_app = ChatApplication(user_id=user_id, max_context_tokens=1000)

    while True:
        user_input = input("\nYou 🧑‍💻: ")
        if user_input.lower() == 'exit':
            print("Ending the chat session. Goodbye!")
            break

        try:
            # Use the chat application to generate a response
            chat_app.chat(user_input)
        except Exception as e:
            print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
