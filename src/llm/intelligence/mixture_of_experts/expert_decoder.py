from typing import Tuple

def expert_llm_decoder(template_name: str) -> Tuple[str, str, float]:
    """
    Decodes an ExpertLLM from the template_name into a model, system prompt, and temperature.

    Args:
        template_name (str): The name of the expert template.

    Returns:
        Tuple[str, str, float]: A tuple containing the model name, system prompt, and temperature.

    Raises:
        ValueError: If the template_name is not found in the expert library.
    """
    expert = EXPERT_LIBRARY.get(template_name)
    if not expert:
        raise ValueError(f"Expert template '{template_name}' not found in the library.")
    
    system_prompt = (
        f"{expert.personality_prompt}\n\n"
        f"Tone: {expert.tone}\n"
        f"Adaptability: {expert.adaptability}\n"
        f"Preferred Response Length: {expert.default_length_preference}\n"
        f"Vocabulary Complexity: {expert.preferred_vocabulary_complexity}\n"
        f"Response Format: {expert.default_response_format}\n\n"
        f"Speaking Instructions: {expert.speaking_instructions}"
    )
    return expert.model, system_prompt, expert.temperature
