import sqlite3


def main():
    conn = sqlite3.connect("medallion_arch.db")
    try:
        # 1. Row count check (fan-out detection)
        print("silver_sales rows:", conn.execute("SELECT COUNT(*) FROM silver_sales").fetchone())
        print("gold_fact_sales rows:", conn.execute("SELECT COUNT(*) FROM gold_fact_sales").fetchone())

        # 2. Grand total comparison: silver (raw) vs gold_fact_sales
        print("silver total (raw NET_PRICE):", conn.execute(
            "SELECT SUM(QUANTITY * NET_PRICE) FROM silver_sales").fetchone())
        print("gold_fact_sales total:", conn.execute(
            "SELECT SUM(total_amount) FROM gold_fact_sales").fetchone())

        # 3. agg fact vs gold_fact_sales total
        print("agg fact total:", conn.execute(
            "SELECT SUM(total_actual_sales) FROM gold_actual_sales_agg_fact").fetchone())

        # 4. rows with date_key = -1 (out of date dim range)
        print("fact rows with date_key=-1:", conn.execute(
            "SELECT COUNT(*) FROM gold_fact_sales WHERE date_key = -1").fetchone())

        # 5. fan-out check: any silver row matching multiple product dim rows?
        print("product fan-out check:", conn.execute("""
            SELECT s.ProductKey, COUNT(*) 
            FROM silver_sales s
            JOIN gold_dim_product p
                ON s.ProductKey = p.product_number
                AND s.ORDER_DATE >= p.change_begin_date
                AND s.ORDER_DATE <= p.change_end_date
            GROUP BY s.ProductKey, s.ORDER_DATE
            HAVING COUNT(*) > 1
            LIMIT 5
        """).fetchall())
        
        print(conn.execute("""
            SELECT product_number, COUNT(*), GROUP_CONCAT(unit_price)
            FROM gold_dim_product
            WHERE product_number = '1'
            GROUP BY product_number
        """).fetchall())
    finally:
        conn.close()


if __name__ == "__main__":
    main()
