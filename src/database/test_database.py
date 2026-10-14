import duckdb

DB_PATH = "data/database/analytics.duckdb"


def main():
    con = duckdb.connect(DB_PATH)

    query = """
        SELECT
            c.customer_name,
            SUM(o.sales_amount) AS revenue
        FROM customers c
        JOIN orders o
            ON c.customer_id = o.customer_id
        WHERE o.status = 'Completed'
        GROUP BY c.customer_name
        ORDER BY revenue DESC
        LIMIT 5
    """

    results = con.execute(query).fetchall()

    print("\nTop 5 Customers by Revenue")
    print("-" * 40)

    for customer, revenue in results:
        print(f"{customer:<25} {revenue:,.2f}")

    con.close()


if __name__ == "__main__":
    main()