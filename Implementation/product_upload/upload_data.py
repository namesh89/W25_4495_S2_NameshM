import os
import pandas as pd
from azure.storage.blob import BlobServiceClient
from azure.data.tables import TableServiceClient, TableEntity
from dotenv import load_dotenv
from config import *
from azure.data.tables import TableServiceClient
from azure.core.credentials import AzureNamedKeyCredential
import base64

# Load environment variables
load_dotenv()

# Create credential object
credential = AzureNamedKeyCredential("AZURE_STORAGE_ACCOUNT_NAME", "AZURE_STORAGE_ACCOUNT_KEY")

# Initialize Azure Clients
blob_service_client = BlobServiceClient(
    account_url=f"https://{AZURE_STORAGE_ACCOUNT_NAME}.blob.core.windows.net",
    credential=AZURE_STORAGE_ACCOUNT_KEY
)
table_service_client = TableServiceClient(
    endpoint=f"https://{AZURE_STORAGE_ACCOUNT_NAME}.table.core.windows.net",
    credential=credential  # Pass the correct credential object
)
table_client = table_service_client.get_table_client(AZURE_TABLE_NAME)

# Function to upload images to Blob Storage
def upload_image_to_blob(blob_name, image_data):
    try:
        blob_client = blob_service_client.get_blob_client(container=AZURE_BLOB_CONTAINER_NAME, blob=f"{AZURE_BLOB_TARGET_DIR}/{blob_name}")
        blob_client.upload_blob(image_data, overwrite=True)
        return f"https://{AZURE_STORAGE_ACCOUNT_NAME}.blob.core.windows.net/{AZURE_BLOB_CONTAINER_NAME}/{AZURE_BLOB_TARGET_DIR}/{blob_name}"
    except Exception as e:
        print(f"Error uploading image {blob_name}: {e}")
        return ""

# Function to decode Base64 image safely
def decode_base64_image(base64_string):
    try:
        if not isinstance(base64_string, str) or base64_string.strip() == "":
            return None  # ✅ Skip empty or non-string values

        # ✅ Clean the Base64 string: remove newlines, spaces, and invalid characters
        base64_string = base64_string.strip().replace("\n", "").replace("\r", "")

        # ✅ Ensure the length is a multiple of 4 (Base64 requires it)
        missing_padding = len(base64_string) % 4
        if missing_padding:
            base64_string += "=" * (4 - missing_padding)

        # ✅ Attempt to decode
        return base64.b64decode(base64_string, validate=True)
    except Exception as e:
        print(f"Error decoding Base64 image: {e} | Data: {base64_string[:30]}...")
        return None  # ✅ Return None if decoding fails

# Function to process the Excel file and upload data
def process_excel_and_upload():
    # ✅ Download Excel file from Azure Blob Storage
    try:
        blob_client = blob_service_client.get_blob_client(AZURE_BLOB_CONTAINER_NAME, f"{AZURE_BLOB_SOURCE_DIR}/Products Table.xlsx")
        blob_data = blob_client.download_blob().readall()
        
        with open("Products Table.xlsx", "wb") as f:
            f.write(blob_data)
    except Exception as e:
        print(f"Error downloading Excel file: {e}")
        return
    
    # ✅ Load Excel file and fill NaN values with empty strings
    df = pd.read_excel("Products Table.xlsx", dtype=str)  # ✅ Read as string to avoid float errors
    df.fillna("", inplace=True)

    # ✅ Process each row
    for index, row in df.iterrows():
        try:
            base64_image = row.get("product_image", "").strip()
            source = row.get("source", "").strip()
            product_category_id = row.get("product_category_id", "").strip()
            product_category = row.get("product_category", "").strip()
            product_description = row.get("product_description", "").strip()
            british_columbia = row.get("british_columbia", "").strip()
            ontario = row.get("ontario", "").strip()
            prince_edward_island = row.get("prince_edward_island", "").strip()
            quebec = row.get("quebec", "").strip()

            # ✅ Handle missing image data properly
            if base64_image == "":
                image_url = ""  # No image available
            else:
                decoded_image = decode_base64_image(base64_image)
                if decoded_image:
                    image_name = f"{product_category_id}_{index}.jpg"
                    image_url = upload_image_to_blob(image_name, decoded_image)
                else:
                    image_url = ""  # If decoding fails, store an empty URL

            # ✅ Store data in Azure Table Storage
            entity = {
                "PartitionKey": "ProductCategory",
                "RowKey": str(index),
                "image_url": image_url,  # ✅ Will be "" if no image is present
                "source": source,
                "product_category_id": product_category_id,
                "product_category": product_category,
                "product_description": product_description,
                "british_columbia": british_columbia,
                "ontario": ontario,
                "prince_edward_island": prince_edward_island,
                "quebec": quebec
            }

            table_client.upsert_entity(entity)
            print(f"Processed row {index+1}")

        except Exception as e:
            print(f"Error processing row {index+1}: {e}")

    print("Upload complete!")

# Run script
if __name__ == "__main__":
    process_excel_and_upload()