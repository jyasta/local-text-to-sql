import duckdb
import sqlglot
from sqlglot import exp


DB_PATH = "data/database/analytics.duckdb"


def get_database_schema():
    """Read tables and columns directly from DuckDB."""

    con = duckdb.connect(DB_PATH)

    tables = con.execute("SHOW TABLES").fetchall()

    schema = {}

    for (table_name,) in tables:

        columns = con.execute(
            f"DESCRIBE {table_name}"
        ).fetchall()

        schema[table_name.lower()] = {
            column[0].lower()
            for column in columns
        }

    con.close()

    return schema


def validate_columns(expression, schema):
    """
    Validate referenced columns.

    SELECT aliases such as total_revenue are allowed
    in ORDER BY and other valid SQL contexts.
    """

    # Collect aliases directly from the SELECT expression
    aliases = set()

    select_node = expression.find(exp.Select)

    if select_node:

        for projection in select_node.expressions:

            if isinstance(projection, exp.Alias):

                aliases.add(
                    projection.alias.lower()
                )

    for column in expression.find_all(exp.Column):

        column_name = column.name.lower()
        table_alias = column.table.lower()

        # Allow SELECT aliases
        if (
            not table_alias
            and column_name in aliases
        ):
            continue

        # --------------------------------------------------
        # Qualified column
        # Example: c.customer_name
        # --------------------------------------------------

        if table_alias:

            real_table = None

            for table in expression.find_all(exp.Table):

                if table.alias_or_name.lower() == table_alias:

                    real_table = table.name.lower()

                    break

            if real_table is None:

                return (
                    False,
                    f"Unknown table or alias '{column.table}'."
                )

            if column_name not in schema[real_table]:

                return (
                    False,
                    f"Column '{column.name}' does not exist "
                    f"in table '{real_table}'."
                )

        # --------------------------------------------------
        # Unqualified column
        # --------------------------------------------------

        else:

            matches = [
                table
                for table, columns in schema.items()
                if column_name in columns
            ]

            if not matches:

                return (
                    False,
                    f"Column '{column.name}' does not exist."
                )

    return True, "Columns are valid."


def validate_sql(sql: str) -> tuple[bool, str]:
    """Validate SQL before execution."""

    sql = sql.strip()

    # --------------------------------------------------
    # Empty SQL
    # --------------------------------------------------

    if not sql:

        return False, "SQL query is empty."

    # --------------------------------------------------
    # Parse SQL
    # --------------------------------------------------

    try:

        statements = sqlglot.parse(
            sql,
            dialect="duckdb"
        )

    except Exception as e:

        return False, f"SQL syntax error: {e}"

    # --------------------------------------------------
    # Only one statement
    # --------------------------------------------------

    if len(statements) != 1:

        return (
            False,
            "Multiple SQL statements are not allowed."
        )

    expression = statements[0]

    # --------------------------------------------------
    # Only SELECT
    # --------------------------------------------------

    if expression.key.upper() != "SELECT":

        return (
            False,
            "Only SELECT queries are allowed."
        )

    # --------------------------------------------------
    # Get schema
    # --------------------------------------------------

    schema = get_database_schema()

    # --------------------------------------------------
    # Validate tables
    # --------------------------------------------------

    for table in expression.find_all(exp.Table):

        table_name = table.name.lower()

        if table_name not in schema:

            return (
                False,
                f"Table '{table.name}' does not exist."
            )

    # --------------------------------------------------
    # Validate columns
    # --------------------------------------------------

    valid, message = validate_columns(
        expression,
        schema
    )

    if not valid:

        return False, message

    return True, "SQL is valid."


if __name__ == "__main__":

    # Valid query
    test_sql = """
    SELECT
        c.customer_name,
        SUM(o.sales_amount) AS total_revenue
    FROM customers c
    JOIN orders o
        ON c.customer_id = o.customer_id
    GROUP BY c.customer_name
    ORDER BY total_revenue DESC
    LIMIT 5
    """

    valid, message = validate_sql(test_sql)

    print("Valid:", valid)
    print("Message:", message)