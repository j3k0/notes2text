# Google Cloud Storage File Uploader

This Python script allows you to upload files to Google Cloud Storage.

## Prerequisites

- Python 3.6+
- Google Cloud Storage account
- Google Cloud Vision API enabled

## Setup

1. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

2. Install the required libraries:
   ```
   pip install -r requirements.txt
   ```

3. Create a Google Cloud project and enable the Cloud Storage API.

4. Create a service account and download the JSON key file:
   - Go to the [Google Cloud Console](https://console.cloud.google.com/)
   - Navigate to "IAM & Admin" > "Service Accounts"
   - Click "Create Service Account"
   - Give it a name and grant it the "Storage Object Creator" role
   - Create a key for this service account and download it as JSON

5. Rename the downloaded JSON file to `service_account.json` and place it in the project directory.

6. Create a bucket in Google Cloud Storage:
   - Go to the Cloud Storage section in the Google Cloud Console
   - Click "Create Bucket" and follow the prompts
   - Note down the bucket name

7. Copy `example.env` to `.env` and update the values:
   ```
   cp example.env .env
   ```
   Then edit `.env` with your specific settings, including the `BUCKET_NAME`.

## Usage

Ensure your virtual environment is activated, then run the script with:

```
python main.py
```

The script will upload the specified file to your Google Cloud Storage bucket.

## Cleanup

```
python cleanup_journal.py
```

## Note

Keep your `service_account.json` file secure and never commit it to version control.
