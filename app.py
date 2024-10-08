import streamlit as st
import pandas as pd
from datetime import datetime
from scripts.firestore_utils import write_document, read_collection, query_collection
import requests
import time

# Base URL for your Flask API
BASE_URL = "https://outbound-bot.onrender.com"

# Initialize Streamlit app layout
st.title("Debt Collection Management Dashboard")

def upload_to_firestore_with_backoff(document_id, data, collection_name, max_retries=5):
    """
    Helper function to upload a document to Firestore with exponential backoff on rate limit errors.
    """
    for attempt in range(max_retries):
        try:
            write_document(collection_name, document_id, data)
            return True
        except Exception as e:
            if "429" in str(e):
                wait_time = 2 ** attempt  # Exponential backoff
                st.warning(f"Rate limit exceeded. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                st.error(f"An error occurred while writing to Firestore: {e}")
                return False
    return False

def upload_contacted(file):
    if file:
        try:
            # Read the CSV file into a pandas DataFrame
            df = pd.read_csv(file)

            # Clean column names: trim and replace spaces with underscores
            df.columns = df.columns.str.strip().str.replace(' ', '_')
            df['Recipient_Number'] = pd.to_numeric(df['Recipient_Number'], errors='coerce').fillna(0).astype(int).astype(str)

            for column in df.columns:
                df[column] = df[column].apply(lambda x: x.split('.')[0] if isinstance(x, str) and '.' in x else x)

            # Log the DataFrame
            st.write("CSV Data Preview:")
            st.write(df)

            # Filter rows where 'status' is 'delivered'
            delivered_df = df[df['Status'].str.lower() == 'delivered']

            # Upload each 'delivered' phone number to Firestore with backoff
            for index, row in delivered_df.iterrows():
                document_id = str(row['Recipient_Number'])
                
                # Prepare data with today's date
                data = {
                    'phone_number': document_id,
                    'date_added': datetime.now().strftime('%Y-%m-%d')
                }

                # Use helper function to write to Firestore with retry on 429 errors
                success = upload_to_firestore_with_backoff(document_id, data, 'contacted_numbers')

                if not success:
                    st.error(f"Failed to upload document: {document_id}")
                    continue

            st.success(f"Uploaded {len(delivered_df)} 'delivered' records to Firestore successfully.")
            log_action("Upload", f"Uploaded {len(delivered_df)} 'delivered' records to Firestore successfully.")

        except Exception as e:
            st.error(f"An error occurred while uploading CSV to Firestore: {e}")
            log_action("Upload", f"Error: {e}")

def update_botfile():
    try:
        botfile_response = requests.get(f"{BASE_URL}/update_botfile")
        if botfile_response.status_code == 200:
            st.success("Botfile updated successfully.")
            st.write(botfile_response.json())
        else:
            st.error("Error updating botfile.")
            st.write(botfile_response.json())
    except Exception as e:
        st.error(f"An error occurred while updating the botfile: {e}")

def upload_payments_to_firestore(file):
    if file:
        try:
            # Read the CSV file into a pandas DataFrame
            df = pd.read_csv(file)

            # Clean column names: trim and replace spaces with underscores
            df.columns = df.columns.str.strip().str.replace(' ', '_')

            # Log the DataFrame
            st.write("Payments CSV Data Preview:")
            st.write(df)

            # Process each row in the DataFrame
            for index, row in df.iterrows():
                contact = str(int(row['Loan_ID']))  # Adjusted for the cleaned column name
                if contact == "":
                    log_action('act2', 'no data')
                    return
                amount_repaid = row['Amount_Repaid']  # Adjusted for the cleaned column name
                log_action('act1', contact)
                
                # Read the corresponding lead from Firestore using Loan ID
                lead_data = query_collection('leads', 'Loan_ID', '==', str(contact))  # Ensure the field and value are correct
                
                if lead_data:
                    log_action('actx', lead_data[0]['id'])
                    # Deduct the Amount Repaid from the updated_amount_deliquent
                    new_delinquent_amount = lead_data[0]['updated_amount_deliquent'] - amount_repaid
                    log_action('act3', lead_data[0]['updated_amount_deliquent'])
                    log_action('act4', amount_repaid)
                    log_action('act5', new_delinquent_amount)
                    lead_data[0]['updated_amount_deliquent'] = new_delinquent_amount
                    updated_lead = lead_data[0]
                    print(new_delinquent_amount)

                    # Update the lead document with the new delinquent amount
                    write_document('leads', lead_data[0]['id'], updated_lead)

                    # Prepare payment data to upload to the payments collection
                    payment_data = row.to_dict()

                    # Upload to the 'payments' collection
                    write_document('payments', contact, payment_data)

            st.success(f"Processed {len(df)} payments and updated Firestore successfully.")
            log_action("Payments Upload", f"Processed {len(df)} payments successfully.")

        except Exception as e:
            st.error(f"An error occurred while processing payments: {e}")
            log_action("Payments Upload", f"Error: {e}")

# Function to upload CSV directly to Firestore
def upload_csv_to_firestore(file):
    if file:
        try:
            # Read the CSV file into a pandas DataFrame
            df = pd.read_csv(file)

            # Clean column names: trim and replace spaces with underscores
            df.columns = df.columns.str.strip().str.replace(' ', '_')
            df['updated_amount_deliquent'] = df['updated_amount_deliquent'].astype(str).str.strip().str.replace(',', '')
            df['updated_amount_deliquent'] = pd.to_numeric(df['updated_amount_deliquent'], errors='coerce').fillna(0)
            df['Loan_ID'] = pd.to_numeric(df['Loan_ID'], errors='coerce').fillna(0).astype(int).astype(str)
            df['Contact_1'] = pd.to_numeric(df['Contact_1'], errors='coerce').fillna(0).astype(int).astype(str)
            df['Contact_2'] = pd.to_numeric(df['Contact_1'], errors='coerce').fillna(0).astype(int).astype(str)

            for column in df.columns:
                df[column] = df[column].apply(lambda x: x.split('.')[0] if isinstance(x, str) and '.' in x else x)

            # Log the DataFrame
            st.write("CSV Data Preview:")
            st.write(df)

            # Upload each row in the DataFrame to Firestore
            for index, row in df.iterrows():
                document_id = str(row['Contact_1'])  # Adjusted for the cleaned column name
                data = row.to_dict()

                # Write each lead to the 'leads' collection
                success = upload_to_firestore_with_backoff(document_id, data, 'leads')

                if not success:
                    st.error(f"Failed to upload document: {document_id}")
                    continue

            st.success(f"Uploaded {len(df)} records to Firestore successfully.")
            log_action("Upload", f"Uploaded {len(df)} records to Firestore successfully.")
        
        except Exception as e:
            st.error(f"An error occurred while uploading CSV to Firestore: {e}")
            log_action("Upload", f"Error: {e}")

# Additional functions for other operations...

def log_action(action, response):
    st.sidebar.text(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: {action}")
    st.sidebar.text(f"Response: {response}")

# File uploader for CSV
uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

# Add buttons for each operation
if st.button("Upload"):
    upload_csv_to_firestore(uploaded_file)

# File uploader for payments CSV
uploaded_payment_file = st.file_uploader("Upload Payments CSV", type=["csv"])

# Add a button for uploading payments
if st.button("Upload Payments"):
    upload_payments_to_firestore(uploaded_payment_file)

# File uploader for contacted CSV
uploaded_contacted_file = st.file_uploader("Upload contacted CSV", type=["csv"])

# Add a button for uploading contacted numbers
if st.button("Upload contacted"):
    upload_contacted(uploaded_contacted_file)

# Monitor logs
st.sidebar.title("Monitor")
st.sidebar.text("Logs will appear here as actions are performed.")




# Function to call initialization endpoint
def initialize():
    try:
        init_response = requests.get(f"{BASE_URL}/initialize")
        if init_response.status_code == 200:
            st.success("Initialization script executed successfully.")
            st.write(init_response.json())
        else:
            st.error("Error executing initialization script.")
            st.write(init_response.json())
    except Exception as e:
        st.error(f"An error occurred: {e}")

# Function to call whatsapp endpoint
def whatsapp():
    try:
        init_response = requests.get(f"{BASE_URL}/whatsapp")
        if init_response.status_code == 200:
            st.success("Initialization script executed successfully.")
            st.write(init_response.json())
        else:
            st.error("Error executing initialization script.")
            st.write(init_response.json())
    except Exception as e:
        st.error(f"An error occurred: {e}")

# Function to call fetch_status endpoint
def check_status():
    try:
        status_response = requests.get(f"{BASE_URL}/fetch_status")
        if status_response.status_code == 200:
            st.success("Status check completed successfully.")
            st.write(status_response.json())
        else:
            st.error("Error checking status.")
            st.write(status_response.json())
    except Exception as e:
        st.error(f"An error occurred: {e}")

# Function to call follow_up endpoint
def follow_up():
    try:
        followup_response = requests.get(f"{BASE_URL}/follow_up")
        if followup_response.status_code == 200:
            st.success("Follow-up script executed successfully.")
            st.write(followup_response.json())
        else:
            st.error("Error executing follow-up script.")
            st.write(followup_response.json())
    except Exception as e:
        st.error(f"An error occurred: {e}")

# Function to log actions and responses
def log_action(action, response):
    st.sidebar.text(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: {action}")
    st.sidebar.text(f"Response: {response}")


if st.button("Initialization"):
    initialize()

if st.button("Whatsapp"):
    whatsapp()

if st.button("Check Status"):
    check_status()

if st.button("Follow-up"):
    follow_up()


