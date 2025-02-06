import csv
from PyPDF2 import PdfReader
import os
import faiss
import numpy as np
from .models import Department

# Load employee data from a CSV file
def load_employee_data(csv_path):
    employee_data = {}
    with open(csv_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            employee_data[row['ID']] = row['Team']
    return employee_data

# Extract department-specific data from a PDF
def extract_pdf_data(pdf_path, chunk_size=300):
    reader = PdfReader(pdf_path)
    content = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            content.extend([text[i:i+chunk_size] for i in range(0, len(text), chunk_size)])
    return content

def generate_embedding(text):
    response = client.embeddings.create(
        model="text-embedding-ada-002",
        input=text
    )
    return np.array(response.data[0].embedding, dtype=np.float32)

def build_faiss_index(text_chunks):
    dimension = 1536  # Embedding size for 'text-embedding-ada-002'
    index = faiss.IndexFlatL2(dimension)
    
    embeddings = []
    for chunk in text_chunks:
        embedding = generate_embedding(chunk)
        embeddings.append(embedding)
    
    embeddings = np.array(embeddings, dtype=np.float32)
    index.add(embeddings)

    return index, text_chunks



def load_all_data():
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    employee_data_path = os.path.join(BASE_DIR, "BotRequestProecessing", 'files', 'New_Age_Employee_Data.csv')
    

    # Load data once
    employee_data = load_employee_data(employee_data_path)
    
    TEXT_CHUNKS = []  
    CHUNK_TO_DEPARTMENT = {}

    

    departments = Department.objects.all()
    for dept in departments:
        pdf_path = os.path.join(settings.MEDIA_ROOT, dept.file.name)
        text_chunks = extract_pdf_data(pdf_path)
        
        for i, chunk in enumerate(text_chunks):
            CHUNK_TO_DEPARTMENT[len(TEXT_CHUNKS) + i] = dept.name  # Map chunk index to department
        
        TEXT_CHUNKS.extend(text_chunks)
    
    # Build a single FAISS index
    FAISS_INDEX = build_faiss_index(TEXT_CHUNKS)
    
    

    return return employee_data, FAISS_INDEX, TEXT_CHUNKS, CHUNK_TO_DEPARTMENT

EMPLOYEE_DATA, FAISS_INDEX, TEXT_CHUNKS, CHUNK_TO_DEPARTMENT = load_all_data()