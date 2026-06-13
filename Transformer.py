import pandas as pd
import sqlite3


class Transformer:
    """
    This class is responsible for transforming the data in the bronze layer and saving it to the silver layer.
    It includes logging of the transformation process, including the start time, end time, processing time
    and details about the number of records and columns transformed.

    Usage:
        Transform.transform_bronze_to_silver(db_file_path)
    """
    def __init__(self):
        pass

    def transform_bronze_to_silver(self, db_file_path):
        """
        Transforms data from bronze layer and saves it to silver layer

        Args:
            db_file_path (str): The path to the SQLite database file.

        Returns:
            None
        """
        # Log the start time of the transformation process
        processing_start_time = pd.Timestamp.now()
        print(f"Starting data transformation from bronze to silver in {db_file_path} at {processing_start_time}")

        # Read data from bronze layer
        df_bronze = pd.read_sql_query("SELECT * FROM bronze_sales", con=sqlite3.connect(db_file_path))

        # Clean and standardize data (e.g., handle nulls, fix data types, trim whitespace, correct invalid values).
        # Remove duplicates
        df_bronze.drop_duplicates(inplace=True)

        # Apply Dead Letter logic (e.g., move invalid records to a separate table or log them for review) - Not asked for it in this assignment, but can be implemented if needed
        # For example, if we want to move records with 0 value in Quantity or Net Price to a separate table called "dead_letter_sales", we can do the following:
        # dead_letter_df = df_bronze[(df_bronze['QUANTITY'] <= 0) | (df_bronze['NET_PRICE'] <= 0)]
        # dead_letter_df.to_sql('dead_letter_sales', con=sqlite3.connect(db_file_path), if_exists='append', index=False)
         

        # Trim whitespace, replace empty strings and NaN  with "Not Provided" and replace regex expressions with Singlespace for all string columns
        for column in df_bronze.select_dtypes(include=['object']).columns:
            # Replace (, , ;, ?, etc.) with a single space => Knowing that just happend in Customer Name, but I applied it to all string columns to be safe
            df_bronze[column] = df_bronze[column].str.replace(r'[,\;\?\(\)]', ' ', regex=True)
            # Trim whitespace
            df_bronze[column] = df_bronze[column].str.strip()
            # Replace empty strings with None => Knowing that just happend in Customer Name, Education & Occupation, but I applied it to all string columns to be safe
            df_bronze[column] = df_bronze[column].replace('', "Not Provided") 
            df_bronze[column] = df_bronze[column].fillna("Not Provided")  # Fill NaN with "Not Provided"

        # Fix data types (Convert ORDER_DATE to datetime, QUANTITY to integer, NET_PRICE to integer after rounding it to the nearest integer)
        df_bronze['ORDERDATE'] = pd.to_datetime(df_bronze['ORDERDATE'], errors='coerce')
        df_bronze['QUANTITY'] = pd.to_numeric(df_bronze['QUANTITY'], errors='coerce').astype('Int64')
        df_bronze['NET_PRICE'] = pd.to_numeric(df_bronze['NET_PRICE'], errors='coerce').round().astype('Int64')
        # Rename columns to be consistent with silver table schema
        df_bronze.rename(columns={
            'CUSTOMERKEY': 'CUSTOMER_KEY',
            'ORDERDATE': 'ORDER_DATE',
            'COUNTRYREGION': 'COUNTRY_REGION'
        }, inplace=True)
        

        # Save transformed data to silver layer
        df_bronze.to_sql('silver_sales', con=sqlite3.connect(db_file_path), if_exists='replace', index=False)

        # Log processing time and details
        processing_end_time = pd.Timestamp.now()
        processing_time = processing_end_time - processing_start_time
        print(f"Data transformation completed in {processing_time.total_seconds() / 60:.2f} minutes.")
        print(f"data transformed from bronze to silver in {db_file_path}")
        print(f"Number of records transformed: {len(df_bronze)}, Number of columns transformed: {len(df_bronze.columns)}")