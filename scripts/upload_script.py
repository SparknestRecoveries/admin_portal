from scripts.firestore_utils import read_collection, write_document
from scripts.cloud_storage_utils import read_csv_from_bucket
import csv
from io import StringIO

def upload_script():
    # Configuration for Google Cloud Storage
    bucket_name = 'your-bucket-name'  # Replace with your bucket name
    csv_filename = 'upload.csv'  # The name of the CSV file in the bucket
    
    # Read CSV data from Google Cloud Storage
    try:
        csv_content = read_csv_from_bucket(bucket_name, csv_filename)
        print(f"Successfully read {csv_filename} from bucket {bucket_name}.")
    except Exception as e:
        print(f"Error reading {csv_filename} from bucket {bucket_name}: {e}")
        return
    
    # Convert the CSV content into a list of dictionaries
    try:
        csv_reader = csv.DictReader(StringIO(csv_content))
        upload_data = list(csv_reader)
        print(f"Parsed CSV data: {upload_data}")
    except Exception as e:
        print(f"Error parsing CSV content: {e}")
        return
    
    # Read existing customers from Firestore
    try:
        customer_data = read_collection('customer')
        print("Successfully read customer data from Firestore.")
    except Exception as e:
        print(f"Error reading customer data from Firestore: {e}")
        return
    
    # Extract customer IDs from Firestore data
    existing_customer_ids = {customer['customer_id'] for customer in customer_data}

    # Identify new customers to add
    new_customers = [row for row in upload_data if row['customer_id'] not in existing_customer_ids]

    # Write new customers to Firestore
    try:
        for customer in new_customers:
            write_document('customer', customer['customer_id'], customer)
        print(f"Successfully added new customers to Firestore: {new_customers}")
    except Exception as e:
        print(f"Error writing new customers to Firestore: {e}")
    
    # Overwrite 'lead' collection in Firestore with the upload data
    try:
        for lead in upload_data:
            write_document('lead', lead['customer_id'], lead)
        print(f"Successfully updated 'lead' collection in Firestore with upload data.")
    except Exception as e:
        print(f"Error updating 'lead' collection in Firestore: {e}")

    print("Upload script completed successfully.")

# Ensure script can be imported without running the function
if __name__ == "__main__":
    upload_script()
