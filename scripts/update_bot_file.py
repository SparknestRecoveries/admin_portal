import os
import json
from datetime import datetime
import openai
from openai import OpenAI
from google.cloud import firestore
from dotenv import load_dotenv
from scripts.firestore_utils import read_collection, write_document

# Initialize OpenAI client
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_ASSISTANT_ID = os.getenv("OPENAI_ASSISTANT_ID")

# Set up the OpenAI API key
openai.api_key = OPENAI_API_KEY

client = OpenAI()

# Initialize Firestore client
db = firestore.Client('OPENAI_ASSISTANT_ID')

def get_most_recent_botfile():
    print(OPENAI_API_KEY)
    """
    Retrieve the most recent entry from the 'botfile' Firestore collection.
    Returns None if there is no document in the collection.
    """
    try:
        collection_ref = db.collection('botfile')
        query = collection_ref.order_by('created_at', direction=firestore.Query.DESCENDING).limit(1)
        docs = query.stream()
        for doc in docs:
            return doc.to_dict()
        return None
    except Exception as e:
        print(f"Error retrieving botfile: {e}")
        return None

def retrieve_leads_and_update_assistant():
    try:
        # Retrieve leads from Firestore
        leads = read_collection('leads')
        print(f"Successfully read leads from Firestore. Total leads: {len(leads)}")
    except Exception as e:
        print(f"Error reading leads from Firestore: {e}")
        return

    leads_file_path = "leads_data.json"
    try:
        with open(leads_file_path, 'w') as f:
            json.dump(leads, f, indent=4)
        print(f"Leads data saved as {leads_file_path}.")
    except Exception as e:
        print(f"Error saving leads data as JSON: {e}")
        return

    # Check for the most recent botfile entry
    most_recent_botfile = get_most_recent_botfile()
    if most_recent_botfile:
        try:
            most_recent_file_id = most_recent_botfile['id']
            openai.File.delete(most_recent_file_id)
            print(f"Successfully deleted the most recent file with ID: {most_recent_file_id}")
        except Exception as e:
            print(f"Error deleting the most recent assistant file: {e}")
    else:
        print("No previous botfile found, skipping the deletion step.")

    # Upload the new file to OpenAI
    try:
        from openai import OpenAI
        response = client.files.create(
        file=open(leads_file_path, "rb"),
        purpose="assistants"
        )
        new_file_id = response.id
        print(f"New file uploaded successfully with ID: {new_file_id}")
    except Exception as e:
        print(f"Error uploading new file to OpenAI: {e}")
        return

    # Link the new file to the assistant
    try:
        vector_store_file = client.beta.vector_stores.files.create(
        vector_store_id="vs_qe45RAGe8i74H58YP0dPWvRy",
        file_id= new_file_id
        )
        print(vector_store_file)
    except Exception as e:
        print(f"Error linking the new file to the assistant: {e}")
        return

    # Store the new file's metadata in the Firestore 'botfile' collection
    try:
        file_doc = {
            'id': new_file_id,
            'created_at': datetime.now().isoformat(),
            'assistant_id': OPENAI_ASSISTANT_ID
        }
        write_document('botfile', f"{new_file_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}", file_doc)
        print("New assistant file metadata stored in Firestore.")
    except Exception as e:
        print(f"Error storing file metadata in Firestore: {e}")

# Run the function
if __name__ == "__main__":
    retrieve_leads_and_update_assistant()
