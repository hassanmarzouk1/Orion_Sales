import sqlite3
import time
from Extractor import Extractor
from Transformer import Transformer
from Loader import Loader
from DB import Medallion

class Pipeline:
    """
    This class is responsible for orchestrating the entire ETL pipeline, including extraction, transformation and loading of data.
    It ensures that each step of the pipeline is executed in the correct order and handles any dependencies between steps.

    Usage:
        Pipeline.run_pipeline()
    """
    def __init__(self):
        pass

    def run_pipeline(self):

        # =========================
        # CONFIGURATION
        # =========================
        DB_FILE = "medallion_arch.db"

        SALES_JSON = "../data/Sales.json"
        FORECAST_JSON = "../data/forecast.json"

        # =========================
        # 1. CREATE DB + TABLES
        # =========================
        print("\n========== SETUP DATABASE ==========")
        dwh = Medallion(db_name=DB_FILE, reset=True)
        dwh.setup_all()
        dwh.close()

        # =========================
        # 2. EXTRACT (JSON → BRONZE)
        # =========================
        print("\n========== EXTRACT ==========")
        extractor = Extractor()
        extractor.extract_json_to_bronze(
            json_file_path=SALES_JSON,
            db_file_path=DB_FILE
        )

        # =========================
        # 3. TRANSFORM (BRONZE → SILVER)
        # =========================
        print("\n========== TRANSFORM ==========")
        transformer = Transformer()
        transformer.transform_bronze_to_silver(DB_FILE)

        # =========================
        # 4. LOAD (SILVER → GOLD)
        # =========================
        print("\n========== LOAD ==========")
        loader = Loader()

        # -------------------------
        # Load Dimensions
        # -------------------------
        print("\n--- Loading Date Dimension ---")
        loader.load_date_dimension(DB_FILE, "gold_dim_date")

        print("\n--- Loading Location Dimension ---")
        loader.load_location_dimension(
            DB_FILE,
            source_table="silver_sales",
            target_table="gold_dim_location"
        )

        print("\n--- Loading Customer Dimension ---")
        loader.load_customer_dimension(
            DB_FILE,
            source_table="silver_sales",
            target_table="gold_dim_customer"
        )

        print("\n--- Loading Year Dimension ---")
        loader.load_year_dimension(
            DB_FILE,
            target_table="gold_dim_year"
        )


        print("\n--- Loading Product Dimension (SCD2) ---")
        loader.load_product_scd2_dimension(
            DB_FILE,
            source_table="silver_sales",
            target_table="gold_dim_product"
        )

        # To update sqlite statistics 
        conn = sqlite3.connect("medallion_arch.db")
        for t in ["silver_sales", "gold_dim_product", "gold_dim_customer", "gold_dim_location", "gold_dim_date","gold_dim_year"]:
            print(t, conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone())

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("ANALYZE;")
        conn.commit()


        # Debugging to see the bottleneck of loading Sales Fact Table
        # print(conn.execute("SELECT ORDER_DATE FROM silver_sales LIMIT 3").fetchall())
        # print(conn.execute("SELECT date FROM gold_dim_date LIMIT 3").fetchall())
        # print(conn.execute("SELECT change_begin_date, change_end_date FROM gold_dim_product LIMIT 3").fetchall())

        # # Explain Query for loading fact table
        # print("\n--- Explain Query for Loading Sales Fact ---")
        # def explain_query(query, db_file_path):
        #     conn = sqlite3.connect(db_file_path)
        #     cursor = conn.cursor()
        #     cursor.execute(f"EXPLAIN QUERY PLAN {query}")
        #     explanation = cursor.fetchall()
        #     conn.close()
        #     return explanation
        
        # query = """
        # INSERT INTO gold_fact_sales (
        #         product_key,
        #         customer_key,
        #         location_key,
        #         date_key,
        #         quantity,
        #         net_price,
        #         total_amount
        #     )
        #     SELECT
        #         COALESCE(p.product_key, -1),
        #         COALESCE(c.customer_key, -1),
        #         COALESCE(l.location_key, -1),
        #         COALESCE(d.date_key, -1),
        #         s.QUANTITY,
        #         s.NET_PRICE,
        #         s.QUANTITY * s.NET_PRICE AS total_amount

        #     FROM 
        #         silver_sales s
        #     LEFT JOIN 
        #         gold_dim_product p
        #             ON s.ProductKey = p.product_number
        #             AND s.ORDER_DATE >= p.change_begin_date
        #             -- AND (p.change_end_date IS NULL OR s.ORDER_DATE <= p.change_end_date)
        #             AND s.ORDER_DATE >= p.change_begin_date
        #             AND s.ORDER_DATE <= p.change_end_date   
        #     LEFT JOIN 
        #         gold_dim_customer c
        #             ON s.CUSTOMER_CODE = c.customer_code
        #     LEFT JOIN 
        #         gold_dim_location l
        #             ON s.CONTINENT = l.CONTINENT
        #             AND s.COUNTRY_REGION = l.COUNTRY_REGION
        #             AND s.CITY = l.CITY
        #             AND s.STATE = l.STATE
        #     LEFT JOIN 
        #         gold_dim_date d
        #             ON d.date = s.ORDER_DATE
        # """
        # explanation = explain_query(query, DB_FILE)
        # print("Query Plan Explanation:")
        # for row in explanation:
        #     print(row)

                    
        # -------------------------
        # Load Fact Table 
        # -------------------------
        print("\n--- Loading Sales Fact ---")
        loader.load_sales_fact(
            DB_FILE,
            source_table="silver_sales",
            target_table="gold_fact_sales"
        )

        # -------------------------
        # Load Aggregated Fact
        # -------------------------
        print("\n--- Loading Aggregated Sales Fact ---")
        loader.load_actual_sales_agg_fact(
            DB_FILE,
            target_table="gold_actual_sales_agg_fact"
        )

        # -------------------------
        # Load Forecast Fact (JSON)
        # -------------------------
        print("\n--- Loading Forecast Fact ---")
        loader.load_forecast_fact(
            DB_FILE,
            json_path=FORECAST_JSON,
            target_table="gold_forecast"
        )

        print("\n------- PIPELINE COMPLETED SUCCESSFULLY --------")


# =========================
# RUN PIPELINE
# =========================
if __name__ == "__main__":
    pipeline = Pipeline()
    pipeline.run_pipeline()