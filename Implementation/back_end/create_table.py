from azure.data.tables import TableServiceClient
from config import Config

# Initialize Table Service Client
table_service = TableServiceClient.from_connection_string(Config.AZURE_STORAGE_CONNECTION_STRING)
table_client = table_service.get_table_client(Config.AZURE_USER_TABLE_NAME)

# Create Table if it doesn't exist
table_client.create_table()
print(f"Table '{Config.AZURE_USER_TABLE_NAME}' is ready.")