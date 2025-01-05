from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials
import os
import csv
import re

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

def trim_data(data):
    """
    Trims rows and columns at the first occurrence of 'eof' and filters out rows containing numbers followed by a period.
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

# Clean and trim the data
values_list = trim_data(values_list)

def format_to_csv(raw_data, output_file):
    """
    Formats raw data into a CSV where each row is one day and the labels are the headers.

    :param raw_data: The raw data as a list of lists.
    :param output_file: The output file path for the formatted CSV.
    """
    # Extract headers (dates) and task labels (column B)
    dates = raw_data[0][2:]  # Dates start from column C
    task_labels = [row[1] for row in raw_data[1:]]  # Task labels are in column B
    task_rows = raw_data[1:]  # Task data starts from row 2

    # Initialize structured data
    formatted_data = []

    # Organize data by day
    for i, date in enumerate(dates):
        if date:  # Ensure the date column is not empty
            day_data = {"Date": date.strip()}
            for label_index, task_row in enumerate(task_rows):
                value = task_row[i + 2] if i + 2 < len(task_row) else ""  # Match task value to the date
                day_data[task_labels[label_index].strip()] = value.strip()
            formatted_data.append(day_data)

    # Write to CSV
    with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["Date"] + [label.strip() for label in task_labels]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(formatted_data)

    print(f"Formatted data written to {output_file}")

def main():
    # Print raw data for verification
    print("Cleaned Data:")
    print(values_list)
    
    # Format the data into a CSV
    output_csv = "formatted_ezchecklist.csv"
    format_to_csv(values_list, output_csv)

if __name__ == "__main__":
    main()
