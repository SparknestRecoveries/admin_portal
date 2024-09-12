from google.cloud import storage

def download_file_from_bucket(bucket_name, source_blob_name, destination_file_name):
    """Download a file from a Google Cloud Storage bucket."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)
    blob.download_to_filename(destination_file_name)
    print(f"File {source_blob_name} downloaded to {destination_file_name}.")

def read_csv_from_bucket(bucket_name, source_blob_name):
    """Read a CSV file directly from a Google Cloud Storage bucket and return its content."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)
    
    content = blob.download_as_text()
    return content
