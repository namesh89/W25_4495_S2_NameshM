import os
import io
import pandas as pd
import uuid
from azure.storage.blob import BlobServiceClient
from azure.data.tables import TableServiceClient, TableClient
from dotenv import load_dotenv
from azure.core.credentials import AzureNamedKeyCredential
from config import config
from flask import Flask

app = Flask(__name__)
app.config.from_object(config)

# Create credential object
credential = AzureNamedKeyCredential(config.AZURE_STORAGE_ACCOUNT_NAME, config.AZURE_STORAGE_ACCOUNT_KEY)

# Azure Storage URLs
BLOB_SERVICE_URL = f"https://{config.AZURE_STORAGE_ACCOUNT_NAME}.blob.core.windows.net/"
TABLE_SERVICE_URL = f"https://{config.AZURE_STORAGE_ACCOUNT_NAME}.table.core.windows.net/"

# Initialize Azure clients
blob_service_client = BlobServiceClient(account_url=BLOB_SERVICE_URL, credential=config.AZURE_STORAGE_ACCOUNT_KEY)
table_service_client = TableServiceClient(endpoint=TABLE_SERVICE_URL, credential=credential)
table_client = table_service_client.get_table_client(table_name=config.AZURE_TABLE_NAME)

# Downloads the Excel file from Azure Blob Storage and loads it into a DataFrame
def download_excel_from_blob():
    try:
        blob_client = blob_service_client.get_blob_client(container=config.AZURE_BLOB_CONTAINER_NAME, blob=config.EXCEL_BLOB_NAME)

        # Check if the blob exists
        if not blob_client.exists():
            raise FileNotFoundError(f"Blob {config.EXCEL_BLOB_NAME} not found in container {config.AZURE_BLOB_CONTAINER_NAME}.")

        download_stream = blob_client.download_blob().readall()
        df = pd.read_excel(io.BytesIO(download_stream), engine='openpyxl')

        return df

    except Exception as e:
        print(f"Error downloading Excel file from Azure Blob Storage: {e}")
        return None

# Filters the required columns, generates unique RowKeys, and adds the image URL column
def filter_and_prepare_data(df):
    # Select only the needed columns and explicitly create a copy
    df = df[["source", "product_id", "product_category", "product_description",
             "british_columbia", "manitoba", "ontario", "prince_edward_island", "quebec"]].copy()

    # Fill missing product_category with "Uncategorized"
    df.loc[:, "product_category"] = df["product_category"].fillna("Uncategorized")

    # Ensure product_category doesn't contain invalid characters like / since it is being used as PartitionKey
    df.loc[:, "product_category"] = df["product_category"].astype(str).str.replace("/", "or", regex=False)

    # Convert product_id to str while keeping blanks as blanks
    df["product_id"] = df["product_id"].fillna("").astype(str).str.strip().str.replace(r"\.0$", "", regex=True)

    # Generate a new unique RowKey for missing product_id
    df["RowKey"] = df["product_id"].apply(lambda x: x if x else str(uuid.uuid4()))  # Generate UUID if empty

    # Add a new column for image URLs
    df.loc[:, "image_url"] = df["product_id"].apply(get_image_url)

    return df

# Checks if an image exists for the product_id and returns the Azure Blob Storage URL
def get_image_url(product_id):
    if not product_id or str(product_id).strip() == "":
        return None  # Skip if product_id is empty

    image_blob_name = f"{config.IMAGES_BLOB_DIR}{product_id}.jpg"  # Assuming images are .jpg

    blob_client = blob_service_client.get_blob_client(container=config.AZURE_BLOB_CONTAINER_NAME, blob=image_blob_name)
    if blob_client.exists():
        return f"{BLOB_SERVICE_URL}{config.AZURE_BLOB_CONTAINER_NAME}/{image_blob_name}"
    
    return None  # No image found

# Uploads the processed data to Azure Table Storage
def upload_data_to_table(df):
    for index, row in df.iterrows():
        try:
            entity = {
                "PartitionKey": row["product_category"],  # Use product_category as PartitionKey
                "RowKey": row["RowKey"],  # Use either product_id or generated UUID as RowKey
                "source": row["source"],
                "product_id": row["product_id"] if pd.notna(row["product_id"]) else "",
                "product_description": row["product_description"] if pd.notna(row["product_description"]) else "",
                "british_columbia": row["british_columbia"] if pd.notna(row["british_columbia"]) else "",
                "manitoba": row["manitoba"] if pd.notna(row["manitoba"]) else "",
                "ontario": row["ontario"] if pd.notna(row["ontario"]) else "",
                "prince_edward_island": row["prince_edward_island"] if pd.notna(row["prince_edward_island"]) else "",
                "quebec": row["quebec"] if pd.notna(row["quebec"]) else "",
                "image_url": row["image_url"] if pd.notna(row["image_url"]) else ""
            }
            table_client.upsert_entity(entity)  # Insert or update entity in Azure Table Storage
        except Exception as e:
            print(f"Error uploading row {index} (RowKey: {row['RowKey']}): {e}")

#Main function to process and upload product data
def main():
    print("Downloading Excel file...")
    df = download_excel_from_blob()
    
    if df is None:
        print("No data to process. Exiting.")
        return

    print("Filtering and preparing data...")
    df = filter_and_prepare_data(df)
    
    print(f"Total rows to upload: {len(df)}")

    print("Uploading data to Azure Table Storage...")
    upload_data_to_table(df)
    
    print("Data upload complete.")

if __name__ == "__main__":
    main()