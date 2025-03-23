from azure.data.tables import TableServiceClient
import pandas as pd
import os
import config  # Ensure this imports correctly
from flask import Flask

# Retrieve configuration from config.py
connection_string = "<<ENTER>>"
table_name = "<<ENTER>>"
output_path = os.path.join(os.path.expanduser('~'), 'Desktop', 'azure_table_data.csv')  # Path to save CSV on desktop

# Connect to the Azure Table Service
table_service = TableServiceClient.from_connection_string(connection_string)
table_client = table_service.get_table_client(table_name)

# Fetch all entities from the table
entities = table_client.list_entities()

# Convert entities to a list of dictionaries
data = [entity for entity in entities]

# Create a DataFrame from the list of dictionaries
df = pd.DataFrame(data)

# Write the DataFrame to a CSV file on the Desktop
df.to_csv(output_path, index=False)

print(f"Data has been successfully downloaded to {output_path}")