import sys
from google.cloud import vision, storage
from google.oauth2 import service_account
import os
from dotenv import load_dotenv
import logging
from google.cloud.storage import Blob, Client
import time
import json

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables from .env file
load_dotenv()
logging.info("Environment variables loaded")

# Get environment variables
service_account_file = os.getenv('SERVICE_ACCOUNT_FILE')
bucket_name = os.getenv('BUCKET_NAME')
default_language_hint = os.getenv('LANGUAGE_HINT', 'en')  # Default to 'en' if not specified

# Check if local file path and optional language hint are provided as arguments
if len(sys.argv) < 2:
    logging.error("No local file path provided")
    logging.error("Usage: python script.py <local_file_path> [language_hint]")
    sys.exit(1)

local_file_path = sys.argv[1]
language_hint = sys.argv[2] if len(sys.argv) > 2 else default_language_hint
destination_blob_name = os.path.basename(local_file_path)
logging.info(f"Processing file: {local_file_path}")
logging.info(f"Using language hint: {language_hint}")

# Initialize clients
logging.info("Initializing Google Cloud clients")
credentials = service_account.Credentials.from_service_account_file(service_account_file)
vision_client = vision.ImageAnnotatorClient(credentials=credentials)
storage_client = storage.Client(credentials=credentials, project=credentials.project_id)
bucket = storage_client.bucket(bucket_name)
blob = bucket.blob(destination_blob_name)

# Check if the blob already exists
if blob.exists():
    logging.warning(f"File {destination_blob_name} already exists in the bucket")
    confirm = input(f"File {destination_blob_name} already exists in the bucket. Do you want to (u)pload again, (c)ontinue processing, or (q)uit? (u/c/q): ").lower()
    if confirm == 'q':
        logging.info("Operation cancelled by user")
        logging.info("Operation cancelled.")
        sys.exit(0)
    elif confirm == 'c':
        logging.info("Continuing with existing file for processing")
        logging.info(f"Continuing with existing file {destination_blob_name} for processing.")
    elif confirm == 'u':
        # Delete the existing blob before uploading
        logging.info(f"Deleting existing file {destination_blob_name} from the bucket")
        blob.delete()
        logging.info(f"Existing file {destination_blob_name} deleted from the bucket.")
    else:
        logging.error("Invalid option selected")
        logging.error("Invalid option. Operation cancelled.")
        sys.exit(1)
else:
    confirm = 'u'  # If file doesn't exist, we'll upload it

# Upload file to GCS if needed
if confirm == 'u':
    logging.info(f"Uploading file {local_file_path} to GCS")
    with open(local_file_path, "rb") as file_obj:
        blob.upload_from_file(file_obj, timeout=300)
    logging.info(f"File {local_file_path} uploaded to {destination_blob_name}.")

else:
    logging.info(f"Skipping upload, using existing file {destination_blob_name}")
    logging.info(f"Using existing file {destination_blob_name} in the bucket.")

# GCS URI of the uploaded file
gcs_source_uri = f"gs://{bucket_name}/{destination_blob_name}"

# Set up the request
batch_size = 2
mime_type = 'application/pdf'
feature = vision.Feature(type=vision.Feature.Type.DOCUMENT_TEXT_DETECTION)

# Use language hint from command-line argument or default
language_hints = [language_hint]

gcs_source = vision.GcsSource(uri=gcs_source_uri)
input_config = vision.InputConfig(gcs_source=gcs_source, mime_type=mime_type)

# Create a unique output directory name based on the input file name
output_directory = os.path.splitext(destination_blob_name)[0]
output_gcs_uri = f"gs://{bucket_name}/{output_directory}/"

# Ensure the output directory exists in the bucket
logging.info(f"Creating output directory: {output_directory}")
output_dir_blob = bucket.blob(f"{output_directory}/")
output_dir_blob.upload_from_string('')

async_request = vision.AsyncAnnotateFileRequest(
    features=[feature],
    input_config=input_config,
    output_config={"gcs_destination": {"uri": output_gcs_uri}},
    image_context=vision.ImageContext(language_hints=language_hints)
)

# Send the request
logging.info(f"Starting text extraction for {destination_blob_name}")
operation = vision_client.async_batch_annotate_files(requests=[async_request])

# Wait for the operation to complete
logging.info("Waiting for text extraction to complete")
response = operation.result(timeout=420)
logging.info("Text extraction completed")

# Process the results
output_file_name = os.path.splitext(destination_blob_name)[0] + '.txt'
logging.info(f"Writing extracted text to {output_file_name}")
with open(output_file_name, 'w', encoding='utf-8') as output_file:
    # List all output files in the bucket
    output_blobs = list(storage_client.bucket(bucket_name).list_blobs(prefix=f'{output_directory}/'))
    
    for output_blob in output_blobs:
        if output_blob.name.endswith('.json'):
            logging.info(f"Processing output file: {output_blob.name}")
            json_string = output_blob.download_as_text()
            
            # Parse the JSON content
            annotation_response = json.loads(json_string)
            
            for page in annotation_response['responses']:
                if 'fullTextAnnotation' in page:
                    text = page['fullTextAnnotation']['text']
                    output_file.write(text)
                    output_file.write('\n\n')  # Add two newlines between pages

logging.info(f"Extracted text has been written to {output_file_name}")

# Ask user if they want to delete the uploaded file
delete_confirm = input(f"Do you want to delete the uploaded file {destination_blob_name} from the bucket? (y/N): ").lower()
if delete_confirm == 'y':
    logging.info(f"Deleting file {destination_blob_name} from the bucket")
    blob.delete()
    logging.info(f"File {destination_blob_name} has been deleted from the bucket")
    logging.info(f"File {destination_blob_name} has been deleted from the bucket.")
else:
    logging.info(f"File {destination_blob_name} remains in the bucket")
    logging.info(f"File {destination_blob_name} remains in the bucket.")

logging.info("Script execution completed")
