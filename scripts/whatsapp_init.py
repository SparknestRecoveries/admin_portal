import json
import os
import requests
from dotenv import load_dotenv
from scripts.firestore_utils import read_collection, write_document
from datetime import datetime

# --------------------------------------------------------------
# Load environment variables
# --------------------------------------------------------------
load_dotenv()

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")  # Your WhatsApp API Access Token
FROM_PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")  # Your WhatsApp phone number ID
VERSION = os.getenv("VERSION")  # Graph API version

# --------------------------------------------------------------
# Function to send a WhatsApp message using the Facebook API
# --------------------------------------------------------------
def send_whatsapp_message(lead):
    url = f"https://graph.facebook.com/{VERSION}/{FROM_PHONE_NUMBER_ID}/messages"
    
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    
    # Data payload for sending a text message
    data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": lead['phone_number'],  # The recipient's WhatsApp phone number
        "type": "text",
        "text": {
            "preview_url": False,  # Disable URL previews
            "body": f'''
                    Hi {lead['Name']}, this is Sparknest.
                    We wanted to remind you that your current balance with Silicon Bank is {lead['updated_amount_deliquent']}. 
                    You can check your loan details on our portal. 
                    If you need assistance or flexible repayment options, feel free to reach out to us anytime. 
                    We're here to support you on your path to debt freedom!
                    '''  # The actual message content
        }
    }
    
    # Send the POST request
    response = requests.post(url, headers=headers, json=data)
    
    # Log the request and response in Firestore (optional)
    write_document('whatsapp_messages', f"{lead['Contact_1']}_{datetime.now().strftime('%Y%m%d%H%M%S')}", {'request_data': data, 'response_status_code': response.status_code, 'response_body': response.text})
    
    # Check for a successful response
    if response.status_code == 200:
        print(f"Message sent successfully to {lead['Contact_1']}: {response.json()}")
        return response.json()
    else:
        print(f"Failed to send message to {llead['Contact_1']}: {response.status_code} {response.text}")
        return None

# --------------------------------------------------------------
# Function to initialize WhatsApp message sending for all leads
# --------------------------------------------------------------
def whatsapp_init():
    # Read leads from Firestore 'leads' collection
    try:
        leads = read_collection('leads')
        print(f"Successfully read leads from Firestore. Total leads: {len(leads)}")
    except Exception as e:
        print(f"Error reading leads from Firestore: {e}")
        return
    
    # Iterate over each lead and send a WhatsApp message
    for lead in leads:
        try:
            response = send_whatsapp_message(lead)
            print(f"WhatsApp message attempt for lead {lead['customer_id']} responded with: {response}")
        except Exception as e:
            print(f"Error sending WhatsApp message to lead {lead['customer_id']}: {e}")

    print("Initialization script completed successfully.")

