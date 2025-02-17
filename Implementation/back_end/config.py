from dotenv import load_dotenv
import os

load_dotenv()
class Config:
    AZURE_STORAGE_ACCOUNT_NAME = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
    AZURE_STORAGE_ACCOUNT_KEY = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
    AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    AZURE_BLOB_CONTAINER_NAME = "lightsproducts"
    AZURE_BLOB_SOURCE_DIR = "lightsproductguide"
    AZURE_BLOB_TARGET_DIR = "lightsproductimages"
    AZURE_USER_TABLE_NAME = "Users"
    AZURE_TEMP_PRODUCT_TABLE_NAME = "LightsProductInquiryTemp"
    EXCEL_FILE_NAME = "Products Table.xlsx"
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "automated_product_inquiry_response_system")

    EXCEL_BLOB_NAME = "lightsproductguide/Products Table.xlsx"
    IMAGES_BLOB_DIR = "lightsproductimages/"