import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DB_CONFIG = {
    'server': os.getenv("DB_SERVER", r"NAMESH\SQLSERVER19"),  # Local SQL Server
    'database': os.getenv("DB_NAME", "product_inquiry"),  # Change to your actual database name
    'username': os.getenv("DB_USER", ""),  # Leave empty for Windows Authentication
    'password': os.getenv("DB_PASSWORD", ""),  # Leave empty for Windows Authentication
    'driver': '{ODBC Driver 17 for SQL Server}',  # Ensure ODBC Driver is installed
    'trusted_connection': 'yes'  # Use Windows Authentication
}