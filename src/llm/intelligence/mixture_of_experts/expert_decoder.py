import csv
from dataclasses import dataclass
from typing import List, Tuple
from src.utils.constants import ExpertLLM

# Define the path to the CSV file
CSV_PATH = "./src/llm/intelligence/mixture_of_experts/experts.csv"

def decode_experts_csv() -> List[ExpertLLM]:
    """Decode the experts CSV and return a list of ExpertLLM objects."""
    experts = []
    try:
        with open(CSV_PATH, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                experts.append(
                    ExpertLLM(
                        template_name=row['template_name'],
                        model=row['model'],
                        temperature=float(row['temperature']),
                        personality_prompt=row['personality_prompt'],
                        speaking_instructions=row['speaking_instructions'],
                        tone=row['tone'],
                        default_length_preference=row['default_length_preference'],
                        preferred_vocabulary_complexity=row['preferred_vocabulary_complexity'],
                        default_response_format=row['default_response_format'],
                        when_to_use=row['when_to_use'],
                        version=int(row['version']),
                    )
                )
    except FileNotFoundError:
        print(f"Error: CSV file not found at {CSV_PATH}. Please check the path.")
    except KeyError as e:
        print(f"Error: Missing column in CSV file: {e}")
    except Exception as e:
        print(f"Error reading CSV file: {e}")
    return experts

def get_expert_selection_info() -> List[Tuple[str, str]]:
    """
    Retrieve the expert names and their 'when to use' descriptions.
    Returns:
        List[Tuple[str, str]]: A list of tuples containing expert names and their 'when to use' descriptions.
    """
    experts = decode_experts_csv()
    return [(expert.template_name, expert.when_to_use) for expert in experts]

def build_system_prompt(expert: ExpertLLM) -> str:
    """Construct the system prompt based on the expert's attributes."""
    return (
        f"You are {expert.template_name}, {expert.personality_prompt}.\n"
        f"Tone: {expert.tone}\n"
        f"Speaking Instructions: {expert.speaking_instructions}\n"
        f"Keeping with what you were asked, your response lengh should be: {expert.default_length_preference}\n"
        f"Your word choice and sentence structure should be: {expert.preferred_vocabulary_complexity}\n"
        f"While keeping with the question you were asked, try to work some of these into your responses: {expert.default_response_format}\n"
    )


def get_expert_by_name(expert_name: str) -> Tuple[str, str, float]:
    """
    Retrieve the model name, system prompt, and temperature for a specific expert.
    Args:
        expert_name (str): Name of the expert to retrieve.
    Returns:
        Tuple[str, str, float]: Model name, system prompt, and temperature.
    """
    experts = decode_experts_csv()
    for expert in experts:
        if expert.template_name == expert_name:
            system_prompt = build_system_prompt(expert)
            return expert.model, system_prompt, expert.temperature
    raise ValueError(f"Expert with name '{expert_name}' not found.")


if __name__ == "__main__":
    # Example usage
    try:
        model_name, system_prompt, temperature = get_expert_by_name("Uncle Iroh")
        print("Model Name:", model_name)
        print("System Prompt:\n", system_prompt)
        print("Temperature:", temperature)
    except ValueError as e:
        print(e)
