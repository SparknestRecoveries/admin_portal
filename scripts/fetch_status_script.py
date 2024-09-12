from scripts.firestore_utils import read_collection, write_document
from datetime import datetime

def get_call_status(call_args):
    """
    Simulate fetching the status of a call.
    This is a placeholder for the actual status retrieval function.
    """
    print(f"Fetching call status for arguments: {call_args}")
    # Simulated response for fetching call status
    response = {
        'lead_id': call_args['lead_id'],
        'status': 'ANSWERED',  # Example statuses: 'ANSWERED', 'NO_ANSWER', 'FAILED'
        'timestamp': datetime.now().isoformat()
    }
    return response

def get_sms_status(sms_args):
    """
    Simulate fetching the status of an SMS.
    This is a placeholder for the actual status retrieval function.
    """
    print(f"Fetching SMS status for arguments: {sms_args}")
    # Simulated response for fetching SMS status
    response = {
        'lead_id': sms_args['lead_id'],
        'status': 'DELIVERED',  # Example statuses: 'DELIVERED', 'FAILED'
        'timestamp': datetime.now().isoformat()
    }
    return response

def fetch_status_script():
    # Read call actions from Firestore 'call_action' collection
    try:
        call_actions = read_collection('call_action')
        print(f"Successfully read call actions from Firestore. Total actions: {len(call_actions)}")
    except Exception as e:
        print(f"Error reading call actions from Firestore: {e}")
        return

    # Read call statuses from Firestore 'call_status' collection
    try:
        call_statuses = read_collection('call_status')
        print(f"Successfully read call statuses from Firestore. Total statuses: {len(call_statuses)}")
    except Exception as e:
        print(f"Error reading call statuses from Firestore: {e}")
        return

    # Read SMS actions from Firestore 'sms_action' collection
    try:
        sms_actions = read_collection('sms_action')
        print(f"Successfully read SMS actions from Firestore. Total actions: {len(sms_actions)}")
    except Exception as e:
        print(f"Error reading SMS actions from Firestore: {e}")
        return

    # Read SMS statuses from Firestore 'sms_status' collection
    try:
        sms_statuses = read_collection('sms_status')
        print(f"Successfully read SMS statuses from Firestore. Total statuses: {len(sms_statuses)}")
    except Exception as e:
        print(f"Error reading SMS statuses from Firestore: {e}")
        return

    # Convert call and SMS statuses to sets for easy lookup
    existing_call_status_ids = {status['id'] for status in call_statuses}
    existing_sms_status_ids = {status['id'] for status in sms_statuses}

    # Process call actions to fetch statuses
    for action in call_actions:
        lead_id = action['id']
        
        # Fetch status only if it hasn't been logged yet
        if lead_id not in existing_call_status_ids:
            try:
                status_response = get_call_status(action)
                print(f"Fetched call status for lead {lead_id}: {status_response}")

                # Log the call status to Firestore
                write_document('call_status', lead_id, status_response)
                print(f"Logged call status for lead {lead_id} in Firestore.")
            except Exception as e:
                print(f"Error fetching or logging call status for lead {lead_id}: {e}")

    # Process SMS actions to fetch statuses
    for action in sms_actions:
        lead_id = action['id']

        # Fetch status only if it hasn't been logged yet
        if lead_id not in existing_sms_status_ids:
            try:
                status_response = get_sms_status(action)
                print(f"Fetched SMS status for lead {lead_id}: {status_response}")

                # Log the SMS status to Firestore
                write_document('sms_status', lead_id, status_response)
                print(f"Logged SMS status for lead {lead_id} in Firestore.")
            except Exception as e:
                print(f"Error fetching or logging SMS status for lead {lead_id}: {e}")

    print("Fetch status script completed successfully.")

if __name__ == "__main__":
    fetch_status_script()
