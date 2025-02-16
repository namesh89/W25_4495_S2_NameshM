from dotenv import load_dotenv
import os

load_dotenv()
class config:
    AZURE_STORAGE_ACCOUNT_NAME = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
    AZURE_STORAGE_ACCOUNT_KEY = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
    AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    AZURE_BLOB_CONTAINER_NAME = "lightsproducts"
    AZURE_BLOB_SOURCE_DIR = "lightsproductguide"
    AZURE_BLOB_TARGET_DIR = "lightsproductimages"
    AZURE_TABLE_NAME = "LightsProductInquiry"
    EXCEL_FILE_NAME = "Products Table.xlsx"

    EXCEL_BLOB_NAME = "lightsproductguide/Products Table.xlsx"
    IMAGES_BLOB_DIR = "lightsproductimages/"