import os
import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
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


def get_entries_with_content_for_n_days(n):
    """
    Fetches entries from the specified Notion database created within the past n days,
    retrieves their content, and formats it as labeled markdown-like output.

    Args:
        n (int): The number of recent days to fetch entries for.

    Returns:
        list: A list of formatted strings, each containing metadata and processed content for an entry.
    """
    # Calculate the start date for the query
    start_date = datetime.now(tz=timezone.utc) - timedelta(days=n)
    start_date_str = start_date.isoformat()  # Format as ISO 8601

    url = f"{BASE_URL}/databases/{DATABASE_ID}/query"
    payload = {
        "filter": {
            "property": "Created",
            "date": {
                "on_or_after": start_date_str  # Filter entries created on or after the start date
            }
        },
        "sorts": [
            {
                "timestamp": "created_time",
                "direction": "descending"  # Most recent first
            }
        ]
    }

    response = requests.post(url, headers=HEADERS, json=payload)

    if response.status_code != 200:
        raise Exception(f"Failed to query Notion database: {response.status_code}, {response.text}")

    data = response.json()
    results = data.get("results", [])

    if not results:
        return []  # Return an empty list if no entries are found

    # Fetch and process each entry
    formatted_entries = []

    for entry in results:
        page_id = entry["id"]
        page_content = retrieve_page_content(page_id)

        # Start with metadata
        formatted_entry = f"# {entry['properties']['Name']['title'][0]['plain_text']} | Created: {entry['properties']['Created']['created_time']}\n"

        def process_blocks(blocks, output):
            """
            Processes blocks to extract journaling questions and answers in a formatted manner.
            """
            last_question = None

            for block in blocks:
                block_type = block.get("type")

                # Heading 2 as a journaling question
                if block_type == "heading_2":
                    # Handle unanswered question
                    if last_question is not None:
                        output += "UserAnswer: user did not answer\n"

                    text = block["heading_2"]["rich_text"]
                    question = "".join([t["plain_text"] for t in text]).strip()
                    output += f"JournalingQuestion: {question}\n"
                    last_question = question

                # Paragraph as an answer
                elif block_type == "paragraph" and last_question is not None:
                    text = block["paragraph"]["rich_text"]
                    answer = "".join([t["plain_text"] for t in text]).strip()
                    output += f"UserAnswer: {answer or 'user did not answer'}\n"
                    last_question = None

                # Process nested blocks in column_list
                elif block_type == "column_list":
                    children = retrieve_child_blocks(block["id"])
                    for child in children:
                        child_blocks = retrieve_child_blocks(child["id"])
                        output = process_blocks(child_blocks, output)

                # Divider
                elif block_type == "divider":
                    if last_question is not None:
                        output += "UserAnswer: user did not answer\n"
                        last_question = None
                    output += "---\n"

            # Handle any remaining unanswered question
            if last_question is not None:
                output += "UserAnswer: user did not answer\n"

            return output

        # Process content
        formatted_entry = process_blocks(page_content, formatted_entry)

        # Append the formatted entry
        formatted_entries.append(formatted_entry)

    return formatted_entries

def get_far_horizon_context():
    """
    Fetches the most recent Far Horizon Context document from the Notion database,
    parses its content, and returns it as key-value pairs.

    Returns:
        dict: A dictionary containing parsed sections of the Far Horizon Context document.
    """
    try:
        # Query the most recent Far-Horizon Context entry
        url = f"{BASE_URL}/databases/{DATABASE_ID}/query"
        payload = {
            "filter": {
                "property": "Name",
                "title": {
                    "equals": "Far Horizon Context"  # Filter by title
                }
            },
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
            raise Exception("No Far-Horizon Context entries found in the database.")

        # Get the page ID of the most recent Far-Horizon Context
        page_id = results[0]["id"]
        page_content = retrieve_page_content(page_id)

        # Parse the content into key-value pairs
        context_data = {}
        current_key = None

        for block in page_content:
            block_type = block.get("type")
            if block_type == "heading_1":  # Section title
                text = block["heading_1"]["rich_text"]
                current_key = "".join([t["plain_text"] for t in text]).strip()
                context_data[current_key] = ""
            elif block_type == "paragraph" and current_key:
                text = block["paragraph"]["rich_text"]
                paragraph_content = "".join([t["plain_text"] for t in text]).strip()
                context_data[current_key] += paragraph_content + " "

        # Clean up whitespace in the values
        context_data = {k: v.strip() for k, v in context_data.items()}
        return context_data

    except Exception as e:
        raise RuntimeError(f"Failed to retrieve Far Horizon Context: {e}")


if __name__ == "__main__":
    # Fetch and print the most recent Far-Horizon Context
    try:
        far_horizon_context = get_far_horizon_context()
        print("Far-Horizon Context:")
        for key, value in far_horizon_context.items():
            print(f"{key}: {value}\n")
    except Exception as e:
        print(f"Error: {e}")