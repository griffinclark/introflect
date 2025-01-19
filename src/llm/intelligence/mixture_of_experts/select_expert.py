import json
import re
from typing import Optional, List, Tuple
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_anthropic import ChatAnthropic
from src.utils.constants import Conversation, ExpertLLM, ChatMessage
from src.llm.intelligence.mixture_of_experts.expert_decoder import get_expert_selection_info, get_expert_by_name

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
            Tuple[bool, str]: TRUE if the expert should be switched, FALSE otherwise, and debug_changes string.
        """
        prompt_template = PromptTemplate(
            input_variables=["last_message", "current_expert"],
            template=(
                "You are a system that determines whether to switch experts during a conversation. "
                "The current expert is: {current_expert}. "
                "The last message is: \"{last_message}\". "
                "Return TRUE if the expert should be switched, otherwise FALSE. Also explain why in plain language."
            )
        )

        chain = LLMChain(llm=self.llm, prompt=prompt_template)
        response = chain.run({"last_message": last_message, "current_expert": current_expert})
        split_response = response.strip().split("\n", 1)
        should_switch = split_response[0].upper() == "TRUE"
        debug_changes = split_response[1] if len(split_response) > 1 else "No explanation provided."
        return should_switch, debug_changes

    def select_expert(self, conversation: Conversation, current_expert: Optional[str] = None) -> ExpertLLM:

        if current_expert:
            last_message = conversation.messages[-1].content if conversation.messages else ""
            should_switch, reason = self.should_switch_expert(last_message, current_expert)
            print(f"Should Switch Expert: {should_switch}, Reason: {reason}")
            if not should_switch:
                expert_data = get_expert_by_name(current_expert)
                print(f"Reusing Current Expert Data: {expert_data}")
                # Ensure the returned expert is an ExpertLLM instance
                if isinstance(expert_data, tuple):
                    return ExpertLLM(
                        template_name=current_expert,
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
                    return ExpertLLM(**expert_data)
                else:
                    raise ValueError(f"Unexpected expert data format: {expert_data}")

        # Analyze the conversation history
        messages = [{"role": msg.role, "content": msg.content} for msg in conversation.messages]
        serialized_history = json.dumps(messages, indent=2)
        print(f"Serialized History: {serialized_history}")

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
        print(f"LLM Response: {response}")

        expert_name = response.split("\n")[0].strip()  # Extract the name of the expert

        # Fetch expert data
        expert_data = get_expert_by_name(expert_name)

        # Ensure the returned expert is an ExpertLLM instance
        if isinstance(expert_data, tuple):
            selected_expert = ExpertLLM(
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
            selected_expert = ExpertLLM(**expert_data)
        else:
            raise ValueError(f"Unexpected expert data format: {expert_data}")

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