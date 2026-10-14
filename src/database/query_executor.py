import duckdb


DB_PATH = "data/database/analytics.duckdb"


class QueryExecutor:

    def __init__(self, db_path=DB_PATH):

        self.db_path = db_path

    # ==========================================================
    # EXECUTE SQL
    # ==========================================================

    def execute(self, sql):

        con = None

        try:

            con = duckdb.connect(
                self.db_path,
                read_only=True
            )

            result = con.execute(sql)

            columns = [
                column[0]
                for column in result.description
            ]

            rows = result.fetchall()

            return {
                "success": True,
                "columns": columns,
                "rows": rows,
                "error": None
            }

        except Exception as e:

            return {
                "success": False,
                "columns": [],
                "rows": [],
                "error": str(e)
            }

        finally:

            if con:

                con.close()


# ==========================================================
# TEST
# ==========================================================

if __name__ == "__main__":

    executor = QueryExecutor()

    sql = """
    SELECT
        c.customer_name,
        SUM(o.sales_amount) AS revenue
    FROM customers c
    JOIN orders o
        ON c.customer_id = o.customer_id
    WHERE o.status = 'Completed'
    GROUP BY c.customer_name
    ORDER BY revenue DESC
    LIMIT 5;
    """

    result = executor.execute(sql)

    if result["success"]:

        print("\nQuery executed successfully.")

        print("\nColumns:")
        print(result["columns"])

        print("\nResults:")
        print("-" * 60)

        for row in result["rows"]:

            print(row)

    else:

        print("\nQuery execution failed.")

        print("Error:")
        print(result["error"])