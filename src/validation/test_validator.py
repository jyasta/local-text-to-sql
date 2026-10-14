from src.validation.sql_validator import validate_sql


def main():

    queries = [
        """
        SELECT
            c.customer_name,
            SUM(o.sales_amount) AS revenue
        FROM customers c
        JOIN orders o
            ON c.customer_id = o.customer_id
        GROUP BY c.customer_name
        ORDER BY revenue DESC
        LIMIT 5
        """,

        """
        DROP TABLE customers
        """
    ]

    for query in queries:

        valid, message = validate_sql(query)

        print("\nQuery:")
        print(query.strip())

        print("\nValid:", valid)
        print("Message:", message)
        print("-" * 60)


if __name__ == "__main__":
    main()