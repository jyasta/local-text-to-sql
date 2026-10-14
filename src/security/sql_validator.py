import sqlglot

ALLOWED_STATEMENTS = {"SELECT", "WITH"}


def validate_sql(sql: str):
    sql = sql.strip()

    if not sql:
        return False, "Empty SQL"

    try:
        parsed = sqlglot.parse_one(sql)

        statement_type = parsed.key.upper()

        if statement_type not in ALLOWED_STATEMENTS:
            return False, "Only SELECT/WITH queries are allowed"

        return True, "Valid SQL"

    except Exception as exc:
        return False, str(exc)


if __name__ == "__main__":
    test_queries = [
        "SELECT * FROM CUSTOMERS",
        "SELECT COUNT(*) FROM ORDERS",
        "DROP TABLE CUSTOMERS",
        "SELECT FROM",
    ]

    for query in test_queries:
        valid, message = validate_sql(query)
        print(f"\nSQL: {query}")
        print(f"Valid: {valid}")
        print(f"Message: {message}")