from dotenv import load_dotenv
import os

load_dotenv()
class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    BACKEND_URL = os.getenv("BACKEND_URL")
    APIRS_SERVICE_API_URL = os.getenv("APIRS_SERVICE_API_URL")

    AZURE_STORAGE_ACCOUNT = os.getenv("AZURE_STORAGE_ACCOUNT")
    AZURE_STORAGE_KEY = os.getenv("AZURE_STORAGE_KEY")
    AZURE_CONTAINER_NAME = os.getenv("AZURE_CONTAINER_NAME")
    AZURE_UPLOAD_FOLDER = os.getenv("AZURE_UPLOAD_FOLDER")