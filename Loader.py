import pandas as pd
import sqlite3


class Loader: 
    """
    This class is responsible for loading data from bronze layer to silver layer & from silver layer to gold layer.
    """
    def __init__(self):
        pass

    def load_bronze_to_silver(self, db_file_path,source_table, target_table):
        """
        Loads data from bronze layer to silver layer

        Args:
            db_file_path (str): The path to the SQLite database file.
            source_table (str): The name of the table to read data from.
            target_table (str): The name of the table to load data into.
        Returns:
            None
        """
        # Read data from bronze layer
        df_bronze = pd.read_sql_query(f"SELECT * FROM {source_table}", con=sqlite3.connect(db_file_path))

        # Write data to silver layer
        df_bronze = df_bronze.to_sql(target_table, con=sqlite3.connect(db_file_path), if_exists="delete_rows", index=False)

    def load_date_dimension(self, db_file_path, target_table):
        """
        Populates the date dimension table.
        
        Args:
            db_file_path (str): The path to the SQLite database file.
            target_table (str): The name of the table to load data into.
        Returns:
            None
        """
        conn = sqlite3.connect(db_file_path)

        # Create date range
        dates = pd.date_range(start='2007-01-01', end='2015-12-31', freq='D')

        # Create DataFrame
        date_dim = pd.DataFrame({'date': dates})

        # Create date_key (YYYYMMDD as int)
        date_dim['date_key'] = date_dim['date'].dt.strftime('%Y%m%d').astype(int)

        # Full date description
        date_dim['full_date_description'] = date_dim['date'].dt.strftime('%A, %d %B %Y')

        # Extract components
        date_dim['day'] = date_dim['date'].dt.day
        date_dim['month'] = date_dim['date'].dt.month
        date_dim['year'] = date_dim['date'].dt.year
        date_dim['quarter'] = date_dim['date'].dt.quarter
        date_dim['week_number'] = date_dim['date'].dt.isocalendar().week.astype(int)

        # Weekday / weekend
        date_dim['is_weekday'] = (date_dim['date'].dt.weekday < 5).astype(int)

        # Holidays (simple example — no holidays)
        date_dim['is_holiday'] = 0

        # Reorder columns to match the schema
        date_dim = date_dim[
            [
                "date_key",
                "date",
                "full_date_description",
                "day",
                "month",
                "year",
                "quarter",
                "week_number",
                "is_holiday",
                "is_weekday"
            ]
        ]
        # Write main data to the database
        date_dim.to_sql(target_table, con=conn, if_exists="replace", index=False)
        
        ####
        # I COULD NOT IMPLEMENT UNKOWN ROW AS POWER BI GAVE ERROR (The date column can't have gaps in dates)
        ####
        # # Insert a row for unknown values with date_key = -1
        # conn.execute(f"""
        #     INSERT INTO {target_table} (
        #         date_key, 
        #         date, 
        #         full_date_description, 
        #         day, 
        #         month, 
        #         year, 
        #         quarter, 
        #         week_number, 
        #         is_holiday, 
        #         is_weekday
        #     )
        #     VALUES (
        #         20061231, 
        #         '2006-01-31', 
        #         'Unknown', 
        #         31, 
        #         12, 
        #         2006, 
        #         4, 
        #         48, 
        #         0, 
        #         1
        #     )
        # """)
        
        conn.commit()
        conn.close()


    def load_year_dimension(self, db_file_path, target_table):
        conn = sqlite3.connect(db_file_path)
        cursor = conn.cursor()

        # Truncate target table before loading 
        cursor.execute(f"DELETE FROM {target_table};")

        # Insert unknown row first
        cursor.execute(f"""
            INSERT INTO {target_table} (YEAR_KEY, YEAR)
            VALUES (-1, 9999);
        """)

        # Insert distinct years from date dimension
        cursor.execute(f"""
            INSERT INTO {target_table} (YEAR_KEY, YEAR)
            SELECT DISTINCT 
                year AS YEAR_KEY,
                year AS YEAR
            FROM gold_dim_date
            WHERE year IS NOT NULL AND year != -1
            ORDER BY year;
        """)
        conn.commit()
        conn.close()      

    def load_location_dimension(self, db_file_path, source_table, target_table):

        conn = sqlite3.connect(db_file_path)
        cursor = conn.cursor()

        # Truncate target table before loading 
        cursor.execute(f"DELETE FROM {target_table};")

        # Insert UNKNOWN row 
        cursor.execute(f"""
            INSERT INTO {target_table} (
                location_key,
                CONTINENT,
                COUNTRY_REGION,
                CITY,
                STATE
            )
            SELECT
                -1,
                'Unknown',
                'Unknown',
                'Unknown',
                'Unknown'
            WHERE NOT EXISTS (
                SELECT 1 FROM {target_table} WHERE location_key = -1
            );
        """)

        # Insert distinct real data with proper keys starting from 1
        cursor.execute(f"""
            INSERT INTO {target_table} (
                location_key,
                CONTINENT,
                COUNTRY_REGION,
                CITY,
                STATE
            )
            SELECT
                ROW_NUMBER() OVER (
                    ORDER BY CONTINENT, COUNTRY_REGION, CITY, STATE
                ) AS location_key,
                CONTINENT,
                COUNTRY_REGION,
                CITY,
                STATE
            FROM (
                SELECT DISTINCT
                    CONTINENT,
                    COUNTRY_REGION,
                    CITY,
                    STATE
                FROM {source_table}
            ) s;
        """)

        conn.commit()
        conn.close()


    def load_customer_dimension(self, db_file_path, source_table, target_table):

        conn = sqlite3.connect(db_file_path)
        cursor = conn.cursor()

        # Truncate target table before loading 
        cursor.execute(f"DELETE FROM {target_table};")

        # Insert UNKNOWN row (only once)
        cursor.execute(f"""
            INSERT INTO {target_table} (
                customer_key,
                customer_number,
                customer_code,
                name,
                education,
                occupation
            )
            SELECT
                -1,
                NULL,
                NULL,
                'Unknown',
                'Unknown',
                'Unknown'
            WHERE NOT EXISTS (
                SELECT 1 FROM {target_table} WHERE customer_key = -1
            );
        """)


        # Insert deduplicated, sorted data with keys starting from 1
        cursor.execute(f"""
            INSERT INTO {target_table} (
                customer_key,
                customer_number,
                customer_code,
                name,
                education,
                occupation
            )
            SELECT
                ROW_NUMBER() OVER (
                    ORDER BY customer_key, customer_code
                ) AS customer_key,
                customer_key as customer_number,
                customer_code,
                name,
                education,
                occupation
            FROM (
                SELECT DISTINCT
                    customer_key,
                    customer_code,
                    name,
                    education,
                    occupation
                FROM {source_table}
            );
        """)

        conn.commit()
        conn.close()


    def load_product_scd2_dimension(self, db_file_path, source_table, target_table):

        conn = sqlite3.connect(db_file_path)
        cursor = conn.cursor()
        
        min_date_row = cursor.execute(
            f"SELECT MIN(DATE(ORDER_DATE)) FROM {source_table}"
        ).fetchone()
        initial_begin_date = min_date_row[0] if min_date_row and min_date_row[0] else '1900-01-01'


        # Insert UNKNOWN product row 
        cursor.execute(f"""
            INSERT INTO {target_table} (
                product_key,
                product_number,
                product_description,
                color,
                brand,
                subcategory,
                category,
                unit_price,
                change_begin_date,
                change_end_date,
                is_current
            )
            SELECT
                -1,
                NULL,
                'Unknown',
                NULL,
                NULL,
                NULL,
                NULL,
                NULL,
                NULL,
                NULL,
                1
            WHERE NOT EXISTS (
                SELECT 1
                FROM {target_table}
                WHERE product_key = -1
            );
        """)

        # Expire changed records
        cursor.execute(f"""
            UPDATE {target_table}
            SET is_current = 0,
                change_end_date = DATE('now')
            WHERE product_number IN (
                SELECT s.productkey
                FROM {source_table} s
                JOIN {target_table} g
                ON s.productkey = g.product_number
                WHERE g.is_current = 1
                AND (
                    s.PRODUCT_NAME != g.product_description OR
                    s.color != g.color OR
                    s.brand != g.brand OR
                    s.subcategory != g.subcategory OR
                    s.category != g.category OR
                    s.NET_PRICE != g.unit_price
                )
            );
        """)

        # Insert new + changed
        cursor.execute(f"""
            INSERT INTO {target_table} (
                product_number,
                product_description,
                color,
                brand,
                subcategory,
                category,
                unit_price,
                change_begin_date,
                change_end_date,
                is_current
            )
            SELECT
                s.ProductKey,
                s.PRODUCT_NAME,
                s.color,
                s.brand,
                s.subcategory,
                s.category,
                s.NET_PRICE,
                ?,
                -- changed from NULL to '9999-12-31' to avoid NULLs in the end date for current records and to speed loading sales fact table
                '9999-12-31',
                1
            -- trying to optimize the query by filtering source data first before joining with the target table to find changed records, instead of joining first and then filtering, which is what caused the performance issue before. This way we reduce the number of rows that need to be compared in the join.
            FROM (
                SELECT
                    ProductKey, PRODUCT_NAME, color, brand, subcategory, category,
                    MAX(NET_PRICE) AS NET_PRICE
                FROM {source_table}
                GROUP BY ProductKey, PRODUCT_NAME, color, brand, subcategory, category
            ) s
            LEFT JOIN {target_table} g
            ON s.ProductKey = g.product_number
            AND g.is_current = 1
            WHERE g.product_number IS NULL
            OR (
                    s.PRODUCT_NAME != g.product_description OR
                    s.color != g.color OR
                    s.brand != g.brand OR
                    s.subcategory != g.subcategory OR
                    s.category != g.category OR
                    s.NET_PRICE != g.unit_price
            );
        """, (initial_begin_date,))

        conn.commit()
        conn.close()


    def load_sales_fact(self, db_file_path, source_table, target_table):

        conn = sqlite3.connect(db_file_path)
        cursor = conn.cursor()

        # Clear fact table
        cursor.execute(f"DELETE FROM {target_table};")

        # Insert fact rows
        cursor.execute(f"""
            INSERT INTO {target_table} (
                product_key,
                customer_key,
                location_key,
                date_key,
                quantity,
                net_price,
                total_amount
            )
            SELECT
                COALESCE(p.product_key, -1),
                COALESCE(c.customer_key, -1),
                COALESCE(l.location_key, -1),
                COALESCE(d.date_key, -1),
                s.QUANTITY,
                s.NET_PRICE,
                s.QUANTITY * s.NET_PRICE

            FROM {source_table} s
            LEFT JOIN gold_dim_product p
                ON s.ProductKey = p.product_number
                AND s.ORDER_DATE >= p.change_begin_date
                AND s.ORDER_DATE <= p.change_end_date

            LEFT JOIN gold_dim_customer c
                ON s.CUSTOMER_CODE = c.customer_code

            LEFT JOIN gold_dim_location l
                ON s.CONTINENT = l.CONTINENT
                AND s.COUNTRY_REGION = l.COUNTRY_REGION
                AND s.CITY = l.CITY
                AND s.STATE = l.STATE

            LEFT JOIN gold_dim_date d
                ON d.date = s.ORDER_DATE
        """)
        conn.commit()
        conn.close()

    def load_actual_sales_agg_fact(self, db_file_path, target_table):

        conn = sqlite3.connect(db_file_path)
        cursor = conn.cursor()

        # Truncate target table before loading 
        cursor.execute(f"DELETE FROM {target_table};")

        # Insert aggregated data from FACT + DIMS
        cursor.execute(f"""
            INSERT INTO {target_table} (
                country_region,
                brand,
                year,
                total_actual_sales
            )
            SELECT

                l.country_region,
                p.brand,
                d.year,

                SUM(f.total_amount) AS total_actual_sales

            FROM 
                gold_fact_sales f
            LEFT JOIN 
                gold_dim_product p
                    ON f.product_key = p.product_key
            LEFT JOIN 
                gold_dim_location l
                    ON f.location_key = l.location_key
            LEFT JOIN 
                gold_dim_date d
                    ON f.date_key = d.date_key
            GROUP BY
                l.country_region,
                p.brand,
                d.year
        """)

        conn.commit()
        conn.close()

    def load_forecast_fact(self, db_file_path, json_path, target_table):

        conn = sqlite3.connect(db_file_path)
        cursor = conn.cursor()

        # Load JSON
        df = pd.read_json(json_path)

        # Create temp table
        df.to_sql("tmp_forecast", conn, if_exists="replace", index=False)

        # Clear target
        cursor.execute(f"DELETE FROM {target_table};")

        # Insert into final table
        cursor.execute(f"""
            INSERT INTO {target_table} (
                country_region,
                brand,
                year,
                forecast
            )
            SELECT
                countryRegion,
                brand,
                year,
                forecast
            FROM tmp_forecast
        """)

        # Drop temp table
        cursor.execute("DROP TABLE tmp_forecast;")

        conn.commit()
        conn.close()

