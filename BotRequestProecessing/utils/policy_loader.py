import os
import requests
import pandas as pd
import msal
import PyPDF2  
import docx  
from openai import OpenAI
from django.conf import settings


# SharePoint API Credentials
TENANT_ID = settings.TENANT_ID
CLIENT_ID = settings.CLIENT_ID
CLIENT_SECRET = settings.CLIENT_SECRET
DOCUMENTS_DRIVE_ID = settings.DOCUMENTS_DRIVE_ID
COMPANY_POLICIES_FOLDER_ID = settings.COMPANY_POLICIES_FOLDER_ID
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPE = ["https://graph.microsoft.com/.default"]

# MSAL Authentication
app = msal.ConfidentialClientApplication(CLIENT_ID, CLIENT_SECRET, AUTHORITY)

# Path for Employee Data
EMPLOYEE_DATA_PATH = os.path.join(settings.BASE_DIR, "BotRequestProecessing", 'files', 'Employees_directory_Feb-06-2025.xlsx')

def get_access_token():
    """Retrieve access token for SharePoint API."""
    token = app.acquire_token_for_client(SCOPE)
    return token.get("access_token")

def list_policy_files():
    """Lists all available policy documents in the Company Policies folder."""
    token = get_access_token()
    headers = {"Authorization": f"Bearer {token}"}
    url = f"https://graph.microsoft.com/v1.0/drives/{DOCUMENTS_DRIVE_ID}/items/{COMPANY_POLICIES_FOLDER_ID}/children"

    response = requests.get(url, headers=headers)
    policy_files = {}

    if response.status_code == 200:
        files = response.json().get("value", [])
        print("\n📂 **Available Policy Files in SharePoint:**")
        for file in files:
            policy_name = file["name"].lower()
            if any(policy_name.endswith(ext) for ext in [".pdf", ".docx"]):  # Process PDFs & DOCX
                print(f"📄 {file['name']} ➝ Downloading...")
                policy_files[policy_name] = file["@microsoft.graph.downloadUrl"]
            else:
                print(f"⚠️ Unsupported file format: {file['name']}")
    else:
        print(f"❌ Error fetching policy files: {response.status_code} - {response.text}")

    return policy_files

def load_employee_data():
    """Load and process employee data from the Excel file."""
    df = pd.read_excel(EMPLOYEE_DATA_PATH, skiprows=4)
    df.columns = ["Name", "Employee ID", "Contract Type", "Team Name", "Department"]
    df = df.dropna(subset=["Employee ID"])
    df["Employee ID"] = df["Employee ID"].astype(str)  # Ensure Employee IDs are strings
    df = df.set_index("Employee ID")
    return df["Contract Type"].to_dict()


def download_policy(policy_url, policy_name):
    """Downloads a policy file and ensures it is valid."""
    # response = requests.get(policy_url, stream=True)
    # if response.status_code == 200:
    #     file_path = os.path.join(settings.BASE_DIR, 'temp', f"{policy_name}")
    #     with open(file_path, "wb") as file:
    #         for chunk in response.iter_content(chunk_size=1024):
    #             file.write(chunk)
    #     return file_path if os.path.getsize(file_path) > 0 else None
    return os.path.join(settings.BASE_DIR, 'temp', f"{policy_name}")

def extract_text(file_path):
    """Extracts text from PDFs and DOCX files."""
    if file_path.endswith(".pdf"):
        try:
            with open(file_path, "rb") as pdf:
                reader = PyPDF2.PdfReader(pdf)
                text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
            return text
        except Exception as e:
            print(f"❌ Error extracting text from {file_path}: {e}")
            return None
    elif file_path.endswith(".docx"):
        try:
            doc = docx.Document(file_path)
            text = "\n".join([para.text for para in doc.paragraphs])
            return text
        except Exception as e:
            print(f"❌ Error extracting text from {file_path}: {e}")
            return None
    return None


EMPLOYEE_DATA = load_employee_data()
POLICY_FILES = list_policy_files()




def preload_policies(policy_files):
    """Downloads and extracts text from all policies once and stores them in memory."""
    POLICY_TEXTS = {}
    policy_files = policy_files

    for policy_name, policy_url in policy_files.items():
        file_path = download_policy(policy_url, policy_name)  # Download once
        if file_path:
            policy_text = extract_text(file_path)  # Extract once
            if policy_text:
                POLICY_TEXTS[policy_name.lower()] = policy_text  # Store in memory

    print("✅ All policies preloaded into memory!")
    return POLICY_TEXTS

POLICY_TEXTS = preload_policies(POLICY_FILES)
