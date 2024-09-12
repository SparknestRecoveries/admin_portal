from google.cloud import firestore
from google.oauth2 import service_account
import os
from dotenv import load_dotenv
import json

# Load the .env file
load_dotenv()

# Get the credentials JSON string from the environment variable
credentials_json = os.getenv("FIRESTORE_CREDENTIALS")

# Convert the string back to a dictionary
credentials_dict = json.loads(credentials_json)

# Initialize the service account credentials
credentials = service_account.Credentials.from_service_account_info(credentials_dict)

# Initialize Firestore client with the credentials
db = firestore.Client(credentials=credentials)


def read_collection(collection_name):
    """Read all documents from a Firestore collection."""
    collection_ref = db.collection(collection_name)
    docs = collection_ref.stream()
    docs_list = []
    for doc in docs:
        doc_dict = doc.to_dict()
        doc_dict['id'] = doc.id
        docs_list.append(doc_dict)
    return docs_list

def write_document(collection_name, document_id, data):
    """Write data to a Firestore document."""
    doc_ref = db.collection(collection_name).document(document_id)
    doc_ref.set(data)

def update_document(collection_name, document_id, data):
    """Update an existing Firestore document."""
    doc_ref = db.collection(collection_name).document(document_id)
    doc_ref.update(data)

def delete_document(collection_name, document_id):
    """Delete a document from Firestore."""
    doc_ref = db.collection(collection_name).document(document_id)
    doc_ref.delete()

def query_collection(collection_name, field_name, operator, value):
    """Query a Firestore collection."""
    collection_ref = db.collection(collection_name)
    query = collection_ref.where(field_name, operator, value)
    docs = query.stream()
    docs_list = []
    for doc in docs:
        doc_dict = doc.to_dict()
        doc_dict['id'] = doc.id
        docs_list.append(doc_dict)
    return docs_list
