import re
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials
import os

# Load environment variables
load_dotenv()

# Google Sheets API setup
scopes = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_file("secrets/google_sheets_service_key.json", scopes=scopes)
client = gspread.authorize(creds)

# Fetch Google Sheet data
sheet_id = os.getenv("EZCHECKLIST_GSHEET_ID")
sheet = client.open_by_key(sheet_id).sheet1
values_list = sheet.get_all_values()

def strip_emojis(text):
    """
    Strips emojis and retains only normal characters, numbers, and common special characters.
    """
    emoji_pattern = re.compile(r"[^\w\s.,:;!?@#&()\-/'\"]+", re.UNICODE)
    return emoji_pattern.sub("", text)

def trim_data(data):
    """
    Trims rows and columns at the first occurrence of 'eof', filters out rows containing numbers followed by a period,
    and strips emojis from all cells.
    """
    # Find the first row that contains "eof" or similar markers
    eof_row_index = None
    for i, row in enumerate(data):
        if any("eof" in str(cell).lower() for cell in row):
            eof_row_index = i
            break

    # Trim rows after "eof"
    if eof_row_index is not None:
        data = data[:eof_row_index]

    # Remove rows containing numbers followed by a period
    number_dot_pattern = re.compile(r"^\d+\.$")
    data = [row for row in data if not any(number_dot_pattern.match(str(cell).strip()) for cell in row)]

    # Strip emojis from all cells
    data = [[strip_emojis(str(cell)) for cell in row] for row in data]

    # Trim columns by checking "eof" or similar in the header row
    if data:
        header_row = data[0]
        col_end = len(header_row)
        for j, cell in enumerate(header_row):
            if "eof" in str(cell).lower():
                col_end = j
                break
        # Trim all rows to the identified column length
        data = [row[:col_end] for row in data]

    return data

def format_to_dict(data):
    """
    Formats raw data into a list of dictionaries.
    Each dictionary represents one day, with task labels as keys.
    Drops any keys that start with a number.
    """
    # Extract headers (dates) and task labels (column B)
    dates = data[0][2:]  # Dates start from column C
    task_labels = [row[1] for row in data[1:]]  # Task labels are in column B
    task_rows = data[1:]  # Task data starts from row 2

    # Initialize structured data
    formatted_data = []

    # Organize data by day
    for i, date in enumerate(dates):
        if date:  # Ensure the date column is not empty
            day_data = {"Date": date.strip()}
            for label_index, task_row in enumerate(task_rows):
                key = task_labels[label_index].strip()
                if not re.match(r"^\d", key):  # Skip keys that start with a number
                    value = task_row[i + 2] if i + 2 < len(task_row) else ""  # Match task value to the date
                    day_data[key] = value.strip()
            formatted_data.append(day_data)

    return formatted_data

def main():
    # Clean and trim the data
    cleaned_data = trim_data(values_list)
    
    # Format the cleaned data into a list of dictionaries
    formatted_data = format_to_dict(cleaned_data)
    
    # Return the cleaned, structured data
    return formatted_data

if __name__ == "__main__":
    cleaned_data = main()
    for entry in cleaned_data[:5]:  # Print the first 5 entries for verification
        print(entry)
