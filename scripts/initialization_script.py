import requests
from scripts.firestore_utils import read_collection, write_document
from datetime import datetime

def post_call(lead_args):
    """
    Make an API call to initiate a call action for a lead.
    """
    url = "https://api.pressone.co/api/third-party/text-to-speech/"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer pk_578161NyyRRLsPoO40jspeTR1bIGA_d28fa8e31bdb11f59b9766c816e17df26d136e22d123d5574d6651f558dacf092fe46ae23a4c9c10afdfd9d977cf3ee86dbae4cef409c8a3007a8afe13ab89ed",  # Replace with your actual API key
    }

    # Prepare the API request payload
    data = {
            "message": f'''
            Hi, this is Sparknest. We're here to help you resolve your balance with Carbon Bank. 
            You can make a payment by depositing into your Silicon Bank account. 
            If you need assistance or want flexible repayment options, contact us. 
            We've sent our details via SMS and WhatsApp. We're here to help!,
            ''',
        "repeats": 1,  # Number of times to repeat the message
        "did": ["02017003095"],  # Lead's phone number
        "numbers": ["+"+str(lead_args['Contact_1'])],  # Lead's phone number
        "session_id": "uuid",  # Optional: Add a unique session ID if necessary
        "callback_url": "https://omi1.ngrok.app/call_webhook"  # Optional: Replace with the actual callback URL
    }

    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()  # Raise an error for 4xx/5xx responses
        result = response.json()
        print(f"Call initiated successfully for lead {lead_args['Contact_1']}: {result}")
        return {
            'status': 'SUCCESS',
            'lead_id': lead_args['Contact_1']
        }
    except requests.exceptions.RequestException as e:
        print(f"Error initiating call for lead {lead_args['Contact_1']}: {e}")
        return {
            'status': 'FAILED',
            'lead_id': lead_args['Contact_1']
        }

def initialization_script():
    # Read leads from Firestore 'leads' collection
    try:
        leads = read_collection('leads')
        print(f"Successfully read leads from Firestore. Total leads: {len(leads)}")
    except Exception as e:
        print(f"Error reading leads from Firestore: {e}")
        return
    
    # Iterate over each lead and initiate a call
    for lead in leads:
        lead_args = lead  # Assuming lead itself has all necessary arguments
        try:
            response = post_call(lead_args)
            print(f"Call attempt for lead {lead['Contact_1']} responded with: {response}")

            # Prepare data to write to 'call_action' Firestore collection
            call_action_data = {
                'lead_id': lead['Contact_1'],
                'timestamp': datetime.now().isoformat(),
                'status': response
            }

            # Write the call action to Firestore
            write_document('call_action', f"{lead['Contact_1']}_{datetime.now().strftime('%Y%m%d%H%M%S')}", call_action_data)
            print(f"Logged call action for lead {lead['Contact_1']} in Firestore.")
        except Exception as e:
            print(f"Error making call or logging action for lead {lead['Contact_1']}: {e}")

    print("Initialization script completed successfully.")


