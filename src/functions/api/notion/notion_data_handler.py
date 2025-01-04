import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Notion API Configuration
NOTION_API_KEY = os.getenv("NOTION_INTEGRATION_SECRET")
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
NOTION_VERSION = "2022-06-28"
BASE_URL = "https://api.notion.com/v1"

if not NOTION_API_KEY:
    raise ValueError("NOTION_INTEGRATION_SECRET is not set in the environment variables.")

# Headers for Notion API
HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": NOTION_VERSION,
}

def query_most_recent_entry():
    """
    Fetches the most recent entry from the specified Notion database for morning journaling exercises.

    Returns:
        dict: The most recent journaling entry, including its properties and content.
    """
    url = f"{BASE_URL}/databases/{DATABASE_ID}/query"
    payload = {
        "sorts": [
            {
                "timestamp": "created_time",  # Sort by creation time
                "direction": "descending"  # Most recent first
            }
        ],
        "page_size": 1  # Only fetch the most recent entry
    }
    response = requests.post(url, headers=HEADERS, json=payload)
    
    if response.status_code != 200:
        raise Exception(f"Failed to query Notion database: {response.status_code}, {response.text}")
    
    data = response.json()
    results = data.get("results", [])
    
    if not results:
        raise Exception("No entries found in the database.")
    
    return results[0]  # Return the most recent entry

def retrieve_page_content(page_id):
    """
    Fetches the full content of a Notion page by its ID.

    Args:
        page_id (str): The ID of the Notion page.

    Returns:
        list: The full content of the Notion page.
    """
    url = f"{BASE_URL}/blocks/{page_id}/children"
    response = requests.get(url, headers=HEADERS)
    
    if response.status_code != 200:
        raise Exception(f"Failed to retrieve page content: {response.status_code}, {response.text}")
    
    data = response.json()
    return data.get("results", [])

def retrieve_child_blocks(block_id):
    """
    Recursively fetches child blocks of a given block ID.

    Args:
        block_id (str): The ID of the Notion block.

    Returns:
        list: A list of child blocks.
    """
    url = f"{BASE_URL}/blocks/{block_id}/children"
    response = requests.get(url, headers=HEADERS)
    
    if response.status_code != 200:
        raise Exception(f"Failed to retrieve child blocks: {response.status_code}, {response.text}")
    
    data = response.json()
    return data.get("results", [])

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Notion API Configuration
NOTION_API_KEY = os.getenv("NOTION_INTEGRATION_SECRET")
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
NOTION_VERSION = "2022-06-28"
BASE_URL = "https://api.notion.com/v1"

if not NOTION_API_KEY:
    raise ValueError("NOTION_INTEGRATION_SECRET is not set in the environment variables.")

# Headers for Notion API
HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": NOTION_VERSION,
}

def query_most_recent_entry():
    url = f"{BASE_URL}/databases/{DATABASE_ID}/query"
    payload = {
        "sorts": [
            {"timestamp": "created_time", "direction": "descending"}
        ],
        "page_size": 1
    }
    response = requests.post(url, headers=HEADERS, json=payload)
    if response.status_code != 200:
        raise Exception(f"Failed to query Notion database: {response.status_code}, {response.text}")
    data = response.json()
    results = data.get("results", [])
    if not results:
        raise Exception("No entries found in the database.")
    return results[0]

def retrieve_page_content(page_id):
    url = f"{BASE_URL}/blocks/{page_id}/children"
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        raise Exception(f"Failed to retrieve page content: {response.status_code}, {response.text}")
    data = response.json()
    return data.get("results", [])

def retrieve_child_blocks(block_id):
    url = f"{BASE_URL}/blocks/{block_id}/children"
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        raise Exception(f"Failed to retrieve child blocks: {response.status_code}, {response.text}")
    data = response.json()
    return data.get("results", [])

def generate_labeled_md():
    try:
        # Fetch the most recent journaling entry
        most_recent_entry = query_most_recent_entry()
        page_id = most_recent_entry['id']
        created_time = most_recent_entry['created_time']
        content = retrieve_page_content(page_id)

        # Initialize the markdown output
        md_output = f"# Most Recent Morning Journaling Entry | Created Time: {created_time}\n"

        def process_blocks(blocks, md_output):
            """
            Process blocks of content to extract questions and answers.
            """
            last_question = None

            for block in blocks:
                block_type = block.get("type")

                # Heading 2 as a journaling question
                if block_type == "heading_2":
                    # If there's an unanswered question, label it
                    if last_question is not None:
                        md_output += f"UserAnswer: user did not answer\n"

                    # Extract question text
                    text = block.get("heading_2", {}).get("rich_text", [])
                    text_content = "".join([part.get("text", {}).get("content", "") for part in text]).strip()
                    md_output += f"JournalingQuestion: {text_content}\n"
                    last_question = text_content

                # Paragraph as an answer
                elif block_type == "paragraph":
                    if last_question is not None:
                        text = block.get("paragraph", {}).get("rich_text", [])
                        text_content = "".join([part.get("text", {}).get("content", "") for part in text]).strip()

                        # Handle empty answers
                        md_output += f"UserAnswer: {text_content or 'user did not answer'}\n"
                        last_question = None

                # Column List (nested blocks)
                elif block_type == "column_list":
                    children = retrieve_child_blocks(block.get("id"))
                    for child in children:
                        column_content = retrieve_child_blocks(child.get("id"))
                        md_output = process_blocks(column_content, md_output)

                # Divider
                elif block_type == "divider":
                    if last_question is not None:
                        md_output += f"UserAnswer: user did not answer\n"
                        last_question = None
                    md_output += "---\n"

            # If there's an unanswered question at the end
            if last_question is not None:
                md_output += f"UserAnswer: user did not answer\n"

            return md_output

        # Process the main content
        md_output = process_blocks(content, md_output)

        return md_output
    except Exception as e:
        return f"An error occurred: {e}"

if __name__ == "__main__":
    print(generate_labeled_md())
