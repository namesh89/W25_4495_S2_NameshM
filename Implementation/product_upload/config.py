from dotenv import load_dotenv
import os

load_dotenv()

AZURE_STORAGE_ACCOUNT_NAME = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
AZURE_STORAGE_ACCOUNT_KEY = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
AZURE_BLOB_CONTAINER_NAME = "lightsproducts"
AZURE_BLOB_SOURCE_DIR = "lightsproductguide"
AZURE_BLOB_TARGET_DIR = "lightsproductimages"
AZURE_TABLE_NAME = "LightsProductInquiry"