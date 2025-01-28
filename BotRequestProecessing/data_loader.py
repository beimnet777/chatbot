import csv
from PyPDF2 import PdfReader

# Load employee data from a CSV file
def load_employee_data(csv_path):
    employee_data = {}
    with open(csv_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            employee_data[row['ID']] = row['Team']
    return employee_data

# Extract department-specific data from a PDF
def extract_pdf_data(pdf_path):
    reader = PdfReader(pdf_path)
    content = ""
    for page in reader.pages:
        content += page.extract_text()
    return content.strip()

# Create the system prompt
def create_system_prompt(employee_data, department_data):
    system_prompt = (
        "You are New Age GPT, a virtual assistant for New Age company. Your responsibilities are:\n"
        "- Authenticate users based on their ID, and verify access to specific department data.\n"
        "- Understand natural user intents, including when users want to end the conversation with phrases like 'thanks,' 'all good,' 'bye,' 'no more help,' or similar.\n"
        "- If the user wants to end the conversation, respond politely and close the session.\n\n"
        "### Employee Data ###\n"
        f"{employee_data}\n\n"
        "### Department Data ###\n"
        f"{department_data}\n\n"
        "Respond naturally, concisely, and professionally at all times."
    )
    return [{"role": "system", "content": system_prompt}]


def load_all_data():
    employee_data_path = '/content/New_Age_Employee_Data.csv'
    it_department_path = '/content/IT_Team_Projects.pdf'
    marketing_department_path = '/content/Marketing_Team_Projects.pdf'

    # Load data once
    employee_data = load_employee_data(employee_data_path)
    it_department_data = extract_pdf_data(it_department_path)
    marketing_department_data = extract_pdf_data(marketing_department_path)

    # Combine department-specific data
    department_data = {
        "IT": it_department_data,
        "Marketing": marketing_department_data,
    }
    
    # Create system prompt 
    conversation = create_system_prompt(employee_data, department_data)

    return conversation

CONVERSATION_PROMPT = load_all_data()