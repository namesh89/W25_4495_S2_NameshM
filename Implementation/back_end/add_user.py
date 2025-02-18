import uuid
from azure.data.tables import TableServiceClient, TableEntity
from config import Config
import bcrypt

# Azure Table connection
table_service = TableServiceClient.from_connection_string(Config.AZURE_STORAGE_CONNECTION_STRING)
user_table = table_service.get_table_client(Config.AZURE_USER_TABLE_NAME)

# Generate a bcrypt hash for a given password
def hash_password(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

# Insert a user into Azure Table Storage
def add_user(email, password):
    user_id = str(uuid.uuid4())  # Generate unique ID
    hashed_password = hash_password(password)

    user_entity = TableEntity()
    user_entity["PartitionKey"] = "users"  # Fixed partition key for all users
    user_entity["RowKey"] = user_id  # Unique identifier for each user
    user_entity["Email"] = email
    user_entity["PasswordHash"] = hashed_password

    user_table.create_entity(user_entity)
    print(f"User {email} added successfully!")

# Run this script with example user
if __name__ == "__main__":
    email = input("Enter email: ")
    password = input("Enter password: ")
    add_user(email, password)