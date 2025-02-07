import pandas as pd
import pyodbc
from sqlalchemy import create_engine
from sqlalchemy import text

excel_file = r"C:\Users\names\OneDrive - Douglas College\Semester 7\Applied Research Project - CSIS4495 002\Original Documents\Products Table.xlsx"

df = pd.read_excel(excel_file)

df.rename(columns={"product_image": "image_url"}, inplace=True)

server = "NAMESH\SQLSERVER19"
database = "product_inquiry"
username = "NAMESH\\names"
trusted_connection = "yes"

conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection={trusted_connection}"

engine = create_engine(f"mssql+pyodbc://@{server}/{database}?driver=SQL+Server+Native+Client+11.0")

try:
    with engine.connect() as connection:
        with connection.begin():
            connection.execute(text("DELETE FROM lights_product_inquiry"))
            connection.execute(text("DBCC CHECKIDENT ('lights_product_inquiry', RESEED, 0)"))
    print("Existing data deleted and ID reset successfully.")
except Exception as e:
    print("Error while deleting data and resetting ID:", e)

try:
    df.to_sql("lights_product_inquiry", engine, if_exists="append", index=False)
    print("Data uploaded successfully.")
except Exception as e:
    print("Error:", e)