import json
import re
from typing import Optional, List, Tuple, Any
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_anthropic import ChatAnthropic
from src.utils.constants import Conversation, ExpertLLM, ChatMessage
from src.llm.intelligence.mixture_of_experts.expert_decoder import get_expert_selection_info, get_expert_by_name
from src.utils.constants import ExpertLLM  # Import the ExpertLLM type

def convert_to_expertLLM(expert_data: Any, expert_name: str) -> ExpertLLM:
    """
    Converts raw expert data (tuple or dict) into an ExpertLLM instance.

    Args:
        expert_data (Any): The raw data for the expert (tuple or dictionary).
        expert_name (str): The name of the expert.

    Returns:
        ExpertLLM: An instance of the ExpertLLM class.
    """
    if isinstance(expert_data, tuple):
        # Map tuple elements to the ExpertLLM type
        return ExpertLLM(
            template_name=expert_name,
            model=expert_data[0],
            temperature=expert_data[2],
            personality_prompt=expert_data[1],
            speaking_instructions="Default speaking instructions",
            tone="Default tone",
            default_length_preference="Default length",
            preferred_vocabulary_complexity="Simple",
            default_response_format="Plain text",
            when_to_use="Default usage",
            version=1
        )
    elif isinstance(expert_data, dict):
        # Initialize directly from a dictionary
        return ExpertLLM(**expert_data)
    else:
        raise ValueError(f"Unexpected format for expert data: {type(expert_data)}")


class ExpertSelector:
    def __init__(self):
        """
        Initializes the ExpertSelector with a LangChain Claude model.
        """
        self.llm = ChatAnthropic(model="claude-3-5-sonnet-20241022", temperature=0.7)

    @staticmethod
    def count_tokens(text: str) -> int:
        """
        Estimates the number of tokens in a given text using regex to split on whitespace.

        Args:
            text (str): The text to count tokens for.

        Returns:
            int: The estimated token count.
        """
        return len(re.findall(r"\S+", text))

    def should_switch_expert(self, last_message: str, current_expert: str) -> Tuple[bool, str]:
        """
        Uses an LLM to decide if the expert should be switched based on the last message.

        Args:
            last_message (str): The content of the last message.
            current_expert (str): The name of the current expert.

        Returns:
            Tuple[bool, str]: A boolean indicating whether to switch experts, and the reasoning provided by the LLM.
        """
        expert_library = get_expert_selection_info()
        prompt_template = PromptTemplate(
            input_variables=["last_message", "current_expert", "expert_library"],
            template=(
                "You are a system that determines whether to switch experts during a conversation. "
                "The current expert is: {current_expert}. "
                "The last message is: \"{last_message}\". "
                "The available experts are: {expert_library}. "
                "Return TRUE if there is a more accurate expert, otherwise FALSE. "
                "Also, provide reasoning explaining your decision."
                "Your response will be parsed with             decision, reasoning = response.split('\n', 1)"
            )
        )

        chain = LLMChain(llm=self.llm, prompt=prompt_template)
        response = chain.run({"last_message": last_message, "current_expert": current_expert, "expert_library": expert_library}).strip()
        # Parse the response into a decision and reasoning
        if "\n" in response:
            decision, reasoning = response.split("\n", 1)
        else:
            decision, reasoning = response, "No reasoning provided."

        decision = decision.strip().upper()
        if decision not in ["TRUE", "FALSE"]:
            reasoning = f"Unexpected response from LLM: {response}"
            print(f"Warning: {reasoning}")
            return False, reasoning

        return decision == "TRUE", reasoning.strip()
   

    def select_expert(self, conversation: Conversation, current_expert: Optional[str] = None) -> Tuple[ExpertLLM, str]:
        """
        Selects the appropriate expert for the conversation.

        Args:
            conversation (Conversation): The conversation history.
            current_expert (Optional[str]): The current expert name, if any.

        Returns:
            Tuple[ExpertLLM, str]: The selected expert and a debug string with reasoning.
        """
        debug_changes = ""

        # Check if there is a current expert
        if current_expert:
            last_message = conversation.messages[-1].content if conversation.messages else ""
            should_switch, reasoning = self.should_switch_expert(last_message, current_expert)

            if not should_switch:
                # Log reasoning for retaining the current expert
                debug_changes = f"Reusing current expert: {current_expert}. Reason: {reasoning}\n"
                expert_data = get_expert_by_name(current_expert)
                selected_expert = convert_to_expertLLM(expert_data, current_expert)
                return selected_expert

            # Log reasoning for switching experts
            debug_changes = f"Switching expert from {current_expert} to a better-suited one. Reason: {reasoning}\n"

        else:
            # Log reasoning for selecting a new expert
            debug_changes = "No current expert assigned. Selecting the best expert for the conversation.\n"

        # Proceed to select a new expert
        messages = [{"role": msg.role, "content": msg.content} for msg in conversation.messages]
        serialized_history = json.dumps(messages, indent=2)

        if self.count_tokens(serialized_history) > 10000:
            raise ValueError("Conversation history exceeds 10,000 tokens.")

        expert_selection_info = get_expert_selection_info()
        prompt_template = PromptTemplate(
            input_variables=["conversation_history", "expert_info"],
            template=(
                "You are a system that selects the best expert for a conversation. "
                "Here is the conversation history (up to 10,000 tokens): \n"
                "{conversation_history}\n\n"
                "Here are the available experts and their descriptions: {expert_info}.\n"
                "Return only the name of the best expert for this conversation."
            )
        )

        chain = LLMChain(llm=self.llm, prompt=prompt_template)
        response = chain.run({
            "conversation_history": serialized_history,
            "expert_info": expert_selection_info
        }).strip()

        expert_name = response.split("\n")[0].strip()  # Extract the name of the expert

        # Fetch expert data and log selection
        expert_data = get_expert_by_name(expert_name)
        selected_expert = convert_to_expertLLM(expert_data, expert_name)
        debug_changes += f"Selected new expert: {expert_name}\n"
        return selected_expert

# Example usage
if __name__ == "__main__":
    # Initialize dependencies
    expert_selector = ExpertSelector()

    # Example conversation
    conversation = Conversation(
        conversation_id="example_conversation",
        user_id="user123",
        messages=[
            ChatMessage(role="user", content="How can I improve my meditation?", expert_used="general", expert_version=1),
        ]
    )

    # Select an expert
    selected_expert, debug_changes = expert_selector.select_expert(conversation, current_expert="Michael McCafferty")
    print("Selected Expert:", selected_expert)
    print("Debug Info:", debug_changes)