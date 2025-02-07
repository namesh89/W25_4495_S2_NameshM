import pandas as pd
import pyodbc
from sqlalchemy import create_engine

products_table = r"C:\Users\names\OneDrive - Douglas College\Semester 7\Applied Research Project - CSIS4495 002\Original Documents\Products Table.xlsx"

df = pd.read_excel(products_table)

#print(df)

server = "NAMESH\SQLSERVER19"
database = "product_inquiry"
username = "NAMESH\\names"
trusted_connection = "yes"  # Windows Authentication

conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection={trusted_connection}"

engine = create_engine(f"mssql+pyodbc://@{server}/{database}?driver=SQL+Server+Native+Client+11.0")

try:
    df.to_sql("lights_product_inquiry", engine, if_exists="append", index=False)
    print("Data uploaded successfully.")
except Exception as e:
    print("Error:", e)