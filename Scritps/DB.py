import sqlite3
import os

class Medallion:
    def __init__(self, db_name="medallion_arch.db", reset=False):
        self.db_name = db_name

        if reset and os.path.exists(db_name):
            os.remove(db_name)

        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()

    # ----------------------
    # Bronze Layer
    # ----------------------
    def create_bronze(self):    
        # enable WAL journal mode for better concurrency
        self.conn.execute("PRAGMA journal_mode = WAL;")
        self.conn.execute("PRAGMA busy_timeout = 5000;")

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS bronze_sales (
            ProductKey INTEGER,
            PRODUCT_NAME TEXT,
            BRAND TEXT,
            COLOR TEXT,
            SUBCATEGORY TEXT,
            CATEGORY TEXT,
            CUSTOMERKEY INTEGER,
            CUSTOMER_CODE TEXT,
            NAME TEXT,
            EDUCATION TEXT,
            OCCUPATION TEXT,
            CONTINENT TEXT,
            CITY TEXT,
            STATE TEXT,
            COUNTRYREGION TEXT,
            ORDERDATE TEXT,
            QUANTITY INTEGER,
            NET_PRICE REAL,
            INGESTION_DATE DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """)

    

        self.conn.commit()
        print("Bronze layer created")

    # ----------------------
    # Silver Layer
    # ----------------------
    def create_silver(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS silver_sales (
            ProductKey INTEGER,
            PRODUCT_NAME TEXT,
            BRAND TEXT,
            COLOR TEXT,
            SUBCATEGORY TEXT,
            CATEGORY TEXT,
            CUSTOMER_KEY INTEGER,
            CUSTOMER_CODE TEXT,
            NAME TEXT,
            EDUCATION TEXT,
            OCCUPATION TEXT,
            CONTINENT TEXT,
            CITY TEXT,
            STATE TEXT,
            COUNTRY_REGION TEXT,
            ORDER_DATE Date,
            QUANTITY INTEGER,
            NET_PRICE REAL,
            INGESTION_DATE DATETIME,
            TRANSFORMED_DATE DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """)

        self.conn.commit()
        print("Silver layer created")

    # ----------------------
    # Gold Layer (DWH)
    # ----------------------
    def create_gold_dwh(self):

        # ======================
        # PRODUCT DIM (SCD2)
        # ======================
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS gold_dim_product (
            product_key INTEGER PRIMARY KEY AUTOINCREMENT,
            product_number TEXT,
            product_description TEXT,
            color TEXT,
            brand TEXT,
            subcategory TEXT,
            category TEXT,
            unit_price REAL,
            change_begin_date TEXT,
            change_end_date TEXT,
            is_current INTEGER
        );
        """)

        # ======================
        # CUSTOMER DIM
        # ======================
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS gold_dim_customer (
            customer_key INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_number TEXT,
            customer_code TEXT,
            name TEXT,
            education TEXT,
            occupation TEXT
        );
        """)

        # ======================
        # LOCATION DIM
        # ======================
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS gold_dim_location (
            location_key INTEGER PRIMARY KEY AUTOINCREMENT,
            continent TEXT,
            country_region TEXT,
            state TEXT,
            city TEXT
        );
        """)

        # ======================
        # DATE DIM
        # ======================
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS gold_dim_date (
            date_key INTEGER PRIMARY KEY,
            date DATE,
            full_date_description TEXT,
            day INTEGER,
            month INTEGER,
            year INTEGER,
            quarter INTEGER,
            week_number INTEGER,
            is_holiday INTEGER,
            is_weekday INTEGER
        );
        """)

        # ======================
        # YEAR DIM (ROll-up Dim)
        # ======================
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS gold_dim_year (
            YEAR_KEY   INT PRIMARY KEY,      
            YEAR       INT NOT NULL          
        );
        """)

        # ======================
        # SALES FACT
        # ======================
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS gold_fact_sales (
            transaction_key integer PRIMARY KEY AUTOINCREMENT,
            product_key INTEGER,
            customer_key INTEGER,
            location_key INTEGER,
            date_key INTEGER,
            quantity INTEGER,
            net_price REAL,
            total_amount REAL,
            FOREIGN KEY (product_key) REFERENCES gold_dim_product(product_key),
            FOREIGN KEY (customer_key) REFERENCES gold_dim_customer(customer_key),
            FOREIGN KEY (location_key) REFERENCES gold_dim_location(location_key),
            FOREIGN KEY (date_key) REFERENCES gold_dim_date(date_key)
        );
        """)

        # ======================
        # FORECAST FACT
        # ======================
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS gold_forecast (
            country_region TEXT,
            brand TEXT,
            forecast REAL,
            year INTEGER,
            PRIMARY KEY (country_region, brand, year),
            FOREIGN KEY (year) REFERENCES gold_dim_DATE(year)
        );
        """)

        # ======================
        # ACTUAL SALES AGG FACT
        # ======================
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS gold_actual_sales_agg_fact (
            country_region TEXT,
            brand TEXT,
            year INTEGER,
            total_actual_sales REAL,                            
            PRIMARY KEY (country_region, brand, year),
            FOREIGN KEY (year) REFERENCES gold_dim_DATE(year)                            
        );
        """)

        self.conn.commit()
        print(" Gold layer (DWH) created")

    # ----------------------
    # Indexing (important for performance)
    # ----------------------
    def create_indexes(self):
        self.cursor.executescript("""
            -- Gold dimension indexes
            CREATE INDEX IF NOT EXISTS idx_product_scd 
            ON gold_dim_product(product_number,change_begin_date, change_end_date);

            -- Added to solve loading sales_fact bottleneck                                  
            CREATE INDEX IF NOT EXISTS idx_product_number_current 
            ON gold_dim_product(product_number, is_current);

            CREATE INDEX IF NOT EXISTS idx_silver_product_order 
            ON silver_sales(ProductKey, ORDER_DATE);                                                                    
            -----                      
            CREATE INDEX IF NOT EXISTS idx_customer_code 
            ON gold_dim_customer(customer_code);

            CREATE INDEX IF NOT EXISTS idx_location_full 
            ON gold_dim_location(continent, country_region, city, state);

            CREATE INDEX IF NOT EXISTS idx_date_date 
            ON gold_dim_date(date);
                                  
            CREATE UNIQUE INDEX IF NOT EXISTS idx_year_dim 
            ON gold_dim_year(YEAR);

            -- Gold fact indexes
            CREATE INDEX IF NOT EXISTS idx_fact_customer
            ON gold_fact_sales(customer_key);

            CREATE INDEX IF NOT EXISTS idx_fact_product
            ON gold_fact_sales(product_key);

            CREATE INDEX IF NOT EXISTS idx_fact_date
            ON gold_fact_sales(date_key);

            -- Silver table indexes
            CREATE INDEX IF NOT EXISTS idx_silver_productkey 
            ON silver_sales(ProductKey);

            CREATE INDEX IF NOT EXISTS idx_silver_orderdate 
            ON silver_sales(Order_Date);

            CREATE INDEX IF NOT EXISTS idx_silver_customercode 
            ON silver_sales(Customer_Code);

            CREATE INDEX IF NOT EXISTS idx_silver_location
            ON silver_sales(Continent, Country_Region, State, City);

            -- Location dimension (duplicate optimized naming)
            CREATE INDEX IF NOT EXISTS idx_location_dim 
            ON gold_dim_location(Continent, Country_Region, State, City);
        """)

        self.conn.commit()
        print("All indexes created successfully")


    # ----------------------
    # Run All
    # ----------------------
    def setup_all(self):
        self.create_bronze()
        self.create_silver()
        self.create_gold_dwh()
        self.create_indexes()
        print("\nFull Medallion + DWH setup completed!")

    def close(self):
        self.conn.close()


# ----------------------
# Usage
# ----------------------
# if __name__ == "__main__":
#     dwh = Medallion(reset=True)
#     dwh.setup_all()
#     dwh.close()
