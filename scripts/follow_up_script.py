from scripts.firestore_utils import read_collection, write_document
from datetime import datetime
from dotenv import load_dotenv
import json
import os

# Load the .env file
load_dotenv()

# Get the credentials JSON string from the environment variable
PRESSONE_TOKEN = os.getenv("PRESSONE_TOKEN")

def post_call(lead_args):
    """
    Make an API call to initiate a call action for a lead.
    """
    url = "https://api.pressone.co/api/third-party/chatterwave/text-to-speech/"
    headers = {
        "Content-Type": "application/json",
        "Authorization": PRESSONE_TOKEN,  # Replace with your actual API key
    }

    # Prepare the API request payload
    data = {
            "message": f'''
            Hi, this is Sparknest. We're here to help you resolve your balance with Carbon Bank. 
            You can make a payment by depositing into your Silicon Bank account. 
            If you need assistance or want flexible repayment options, contact us. 
            We've sent our details via SMS and WhatsApp. We're here to help!,
            ''',
        "repeats": 3,  # Number of times to repeat the message
        "did": [lead_args['Contact_1']],  # Lead's phone number
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

def post_sms(lead_args):
    url = "https://BASE_URL/api/sms/send"
    payload = {
            "to": {lead_args['Contact_1']},
            "from": "2348090653657",
            "sms": f'''
                    Hi {lead_args['Name']}, this is Sparknest.
                    Your balance with Silicon Bank is N{lead_args['updated_amount_deliquent']}. 
                    Check your loan details online or contact us for assistance. We're here to help!
                    ''',
            "type": "plain",
            "channel": "generic",
            "api_key": "Your API Key",
                "media": {
                    "url": "",
                    "caption": ""
                }   
        }
    headers = {
    'Content-Type': 'application/json',
    }
    response = requests.request("POST", url, headers=headers, json=payload)
    print(response.text)
    return response

def follow_up_script():
    # Read call status from Firestore 'call_status' collection
    try:
        call_statuses = read_collection('call_status')
        print(f"Successfully read call statuses from Firestore. Total records: {len(call_statuses)}")
    except Exception as e:
        print(f"Error reading call statuses from Firestore: {e}")
        return

    # Read SMS status from Firestore 'sms_status' collection
    try:
        sms_statuses = read_collection('sms_status')
        print(f"Successfully read SMS statuses from Firestore. Total records: {len(sms_statuses)}")
    except Exception as e:
        print(f"Error reading SMS statuses from Firestore: {e}")
        return

    # Dictionary to keep track of call and SMS attempts
    call_attempts = {}
    sms_attempts = set()

    # Process call statuses to determine follow-up actions
    for status in call_statuses:
        customer_id = status['lead_id']# change to format of response
        state = status.get('status', '')
        
        if customer_id not in call_attempts:
            call_attempts[customer_id] = {'answered': 0, 'attempts': 0}
        
        call_attempts[customer_id]['attempts'] += 1
        if state == "ANSWERED":
            call_attempts[customer_id]['answered'] += 1
    
    # Process SMS statuses to determine if SMS was sent
    for status in sms_statuses:
        customer_id = status['lead_id']
        sms_attempts.add(customer_id)

    # Determine follow-up actions based on statuses
    for customer_id, attempts in call_attempts.items():
        if attempts['answered'] == 0:
            # If the customer has never answered a call, schedule another call attempt
            call_customer_args = {'customer_id': customer_id}
            try:
                #response = post_call(call_customer_args)
                response = {# Placeholder
                'lead_id': customer_id,
                'timestamp': datetime.now().isoformat(),
                'status': "FAILED"
                }
                print(f"Follow-up call attempt for customer {customer_id} responded with: {response}")

                # Log follow-up call attempt to Firestore
                call_log_data = {
                    'lead_id': customer_id,
                    'timestamp': datetime.now().isoformat(),
                    'status': response['status']
                }
                write_document('call_action', f"{customer_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}", call_log_data)
                print(f"Logged follow-up call action for customer {customer_id} in Firestore.")

            except Exception as e:
                print(f"Error making follow-up call or logging action for customer {customer_id}: {e}")

        elif attempts['answered'] > 0 and customer_id not in sms_attempts:
            # If the customer has answered a call but has not been sent an SMS, send an SMS
            sms_customer_args = {'customer_id': customer_id}
            try:
                #response = post_sms(sms_customer_args)
                response = {# Placeholder
                'lead_id': customer_id,
                'timestamp': datetime.now().isoformat(),
                'status': "FAILED"
                }
                print(f"Follow-up SMS attempt for customer {customer_id} responded with: {response}")

                # Log SMS attempt to Firestore
                sms_log_data = {
                    'lead_id': customer_id,
                    'timestamp': datetime.now().isoformat(),
                    'status': response['status']
                }
                write_document('sms_action', f"{customer_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}", sms_log_data)
                print(f"Logged SMS action for customer {customer_id} in Firestore.")

            except Exception as e:
                print(f"Error sending SMS or logging action for customer {customer_id}: {e}")

    print("Follow-up script completed successfully.")

