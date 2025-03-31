import io
import pandas as pd
import uuid
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from azure.data.tables import TableServiceClient
from azure.core.credentials import AzureNamedKeyCredential
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
from flask import Flask
import numpy as np
import base64
import requests
from PIL import Image
from tensorflow.keras.applications.resnet50 import ResNet50, preprocess_input
from tensorflow.keras.preprocessing import image
from sentence_transformers import SentenceTransformer
from config import config
from io import BytesIO


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

# Models for embeddings
model_pc = SentenceTransformer('all-mpnet-base-v2')
model_pd = SentenceTransformer('bert-large-nli-stsb-mean-tokens')
model_img = ResNet50(weights='imagenet', include_top=False, pooling='avg')

def encode_array(arr):
    return base64.b64encode(arr.astype(np.float32).tobytes()).decode('utf-8')

# Downloads the Excel file from Azure Blob Storage and loads it into a DataFrame
def download_excel_from_blob():
    try:
        blob_client = blob_service_client.get_blob_client(container=config.AZURE_BLOB_CONTAINER_NAME, blob=config.EXCEL_BLOB_NAME)

        # Check if the blob exists
        if not blob_client.exists():
            raise FileNotFoundError(f"Blob {config.EXCEL_BLOB_NAME} not found in container {config.AZURE_BLOB_CONTAINER_NAME}.")

        download_stream = blob_client.download_blob().readall()
        df = pd.read_excel(io.BytesIO(download_stream), engine='openpyxl')

        # Original row count
        total_rows = len(df)

        # Filter rows where 'product_id' is not null or empty
        df = df[df['product_id'].notna() & (df['product_id'].astype(str).str.strip() != '')]

        # Filtered row count
        filtered_rows = len(df)
        removed_rows = total_rows - filtered_rows

        print(f"{removed_rows} rows were filtered out due to missing or empty 'product_id'. {filtered_rows} rows returned.")

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

    extensions = ["jpg", "jpeg", "png"]  # Possible file extensions
    for ext in extensions:
        image_blob_name = f"{config.IMAGES_BLOB_DIR}{product_id}.{ext}"

        blob_client = blob_service_client.get_blob_client(container=config.AZURE_BLOB_CONTAINER_NAME, blob=image_blob_name)

        try:
            # Generate SAS token with read permissions
            sas_token = generate_blob_sas(
                account_name=config.AZURE_STORAGE_ACCOUNT_NAME,
                container_name=config.AZURE_BLOB_CONTAINER_NAME,
                blob_name=image_blob_name,
                account_key=config.AZURE_STORAGE_ACCOUNT_KEY,
                permission=BlobSasPermissions(read=True),
                expiry=datetime.now(timezone.utc) + relativedelta(years=100)  # 100 years expiry
            )

            # Construct the SAS URL
            image_url = f"https://{config.AZURE_STORAGE_ACCOUNT_NAME}.blob.core.windows.net/{config.AZURE_BLOB_CONTAINER_NAME}/{image_blob_name}?{sas_token}"

            blob_client.download_blob().readall()  # Try fetching the image
            return image_url
        
        except:
            continue  # Try next extension

    print(f"Image not found for product_id {product_id}.")
    return None

# Deletes all records from the Azure Table before inserting new data
def delete_all_records_in_table():
    try:
        entities = list(table_client.list_entities())  # Fetch all entities
        count = 0
        for entity in entities:
            table_client.delete_entity(partition_key=entity["PartitionKey"], row_key=entity["RowKey"])
            count += 1
        print(f"Deleted {count} existing records successfully.")
    except Exception as e:
        print(f"Error deleting existing records: {e}")

def compute_image_embedding(image_url):
    try:
        response = requests.get(image_url, timeout=10)
        img = Image.open(BytesIO(response.content)).convert('RGB')
        img = img.resize((224, 224))
        img_array = image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0)
        img_array = preprocess_input(img_array)
        return model_img.predict(img_array)[0]
    except Exception as e:
        print(f"Error processing image {image_url}: {e}")
        return np.zeros((2048,), dtype=np.float32)

# Uploads the processed data to Azure Table Storage
def upload_data_to_table(df):
    for index, row in df.iterrows():
        try:
            # Compute embeddings
            pc_embedding = model_pc.encode(row["product_category"])
            pd_embedding = model_pd.encode(row["product_description"] if pd.notna(row["product_description"]) else "")
            img_embedding = compute_image_embedding(row["image_url"]) if row["image_url"] else np.zeros((2048,), dtype=np.float32)

            # Build the entity for Azure Table Storage
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
                "image_url": row["image_url"] if pd.notna(row["image_url"]) else "",

                # Encode and store embeddings
                "text_embedding_pc": encode_array(pc_embedding),
                "text_embedding_pd": encode_array(pd_embedding),
                "image_embedding": encode_array(img_embedding)
            }

            # Upload to Azure Table Storage
            table_client.upsert_entity(entity)

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

    print("Deleting existing records from Azure Table Storage...")
    delete_all_records_in_table()

    print("Uploading data to Azure Table Storage...")
    upload_data_to_table(df)
    
    print("Data upload complete.")

if __name__ == "__main__":
    main()