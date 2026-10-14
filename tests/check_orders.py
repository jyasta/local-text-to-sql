import duckdb

DB_PATH = "data/database/analytics.duckdb"

con = duckdb.connect(DB_PATH, read_only=True)

print("\n2025 COMPLETED REVENUE")
print("=" * 50)

result = con.execute("""
    SELECT
        SUM(sales_amount) AS total_revenue
    FROM orders
    WHERE order_date >= '2025-01-01'
      AND order_date < '2026-01-01'
      AND status = 'Completed'
""").fetchall()

print(result)

con.close()