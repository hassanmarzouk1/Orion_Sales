import json
import sqlite3
import pandas as pd
import csv


class Extractor:
    """
    This class is responsible for extracting data from a JSON file and saving it as a CSV file in the bronze layer.
    It includes logging of the extraction process, including the start time, end time, processing time
    and details about the number of records and columns extracted.

    Usage:
        Extract.extract_json_to_csv(json_file_path, db_file_path)
    """
    def __init__(self):
        pass

    def extract_json_to_bronze(self,json_file_path,db_file_path):
        """
        Extracts Json file and load it as it is in csv format (bronze layer)

        Args:
            json_file_path (str): The path to the input JSON file.
            db_file_path (str): The path to the output SQLite database file.

        Returns:
            None
        """
        # Log the start time of the extraction process
        processing_start_time = pd.Timestamp.now()
        print(f"Starting data extraction from {json_file_path} to {db_file_path} at {processing_start_time}")

        # Read JSON file
        with open(json_file_path, 'r', encoding='utf-8') as json_file:
           data = json.load(json_file)

        # Convert to DataFrame
        df = pd.DataFrame(data)

        # Rename columns to be consistent with table schema
        df.columns = [col.strip().replace(" ", "_").replace("-", "_").upper() 
                     for col in df.columns]
        
        # (Used the commented code below for debugging and understanding the data structure)
            # print(df.dtypes)
            # print(df.head())
            # print(df.describe(include='all'))
            # df.info()
        # Save to CSV file in bronze layer
        #csv_file_path = "../data/bronze_sales.csv"
        # df.to_csv(csv_file_path, index=False, encoding='utf-8')


        df.to_sql('bronze_sales', con=sqlite3.connect(db_file_path), if_exists='append', index=False)

        # Log processing time and details
        processing_end_time = pd.Timestamp.now()
        processing_time = processing_end_time - processing_start_time
        print(f"Data extraction completed in {processing_time.total_seconds() / 60:.2f} minutes.")
        # print(f"data extracted from {json_file_path} and saved to {db_file_path}")
        print(f"Number of records extracted: {len(df)}, Number of columns extracted: {len(df.columns)}")

# Run Extractor as a standalone script for testing
# if __name__ == "__main__":
    # Example usage
    #extractor = Extractor()
    # extractor.extract_json_to_bronze(
    #     json_file_path="../data/Sales.json",
    #     csv_file_path="../data/bronze_sales.csv"
    # )




