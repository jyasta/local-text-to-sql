import duckdb

DB_PATH = "data/database/analytics.duckdb"


def get_schema():

    con = duckdb.connect(DB_PATH, read_only=True)

    tables = con.execute(
        "SHOW TABLES"
    ).fetchall()

    schema = {}

    for table_row in tables:

        table_name = table_row[0]

        columns = con.execute(
            f"DESCRIBE {table_name}"
        ).fetchall()

        schema[table_name] = []

        for column in columns:

            column_name = column[0]
            data_type = column[1]

            column_info = {
                "name": column_name,
                "type": data_type
            }

            # --------------------------------------------
            # Retrieve categorical values
            # --------------------------------------------

            if data_type.upper() in (
                "VARCHAR",
                "TEXT"
            ):

                try:

                    values = con.execute(
                        f"""
                        SELECT DISTINCT "{column_name}"
                        FROM "{table_name}"
                        WHERE "{column_name}" IS NOT NULL
                        LIMIT 20
                        """
                    ).fetchall()

                    column_info["values"] = [
                        row[0]
                        for row in values
                    ]

                except Exception:

                    column_info["values"] = []

            schema[table_name].append(
                column_info
            )

    con.close()

    return schema


def print_schema(schema):

    print("\nDATABASE SCHEMA")
    print("=" * 60)

    for table_name, columns in schema.items():

        print(f"\nTable: {table_name}")
        print("-" * 40)

        for column in columns:

            print(
                f"  {column['name']:<25} "
                f"{column['type']}"
            )

            if column.get("values"):

                print(
                    f"    Values: "
                    f"{column['values']}"
                )


if __name__ == "__main__":

    schema = get_schema()

    print_schema(schema)