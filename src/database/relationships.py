RELATIONSHIPS = [
    {
        "from_table": "customers",
        "from_column": "customer_id",
        "to_table": "orders",
        "to_column": "customer_id",
    },
    {
        "from_table": "employees",
        "from_column": "employee_id",
        "to_table": "orders",
        "to_column": "employee_id",
    },
    {
        "from_table": "orders",
        "from_column": "order_id",
        "to_table": "order_items",
        "to_column": "order_id",
    },
    {
        "from_table": "products",
        "from_column": "product_id",
        "to_table": "order_items",
        "to_column": "product_id",
    },
]


def get_relationship_text():

    lines = []

    for relationship in RELATIONSHIPS:

        lines.append(
            f"{relationship['from_table']}."
            f"{relationship['from_column']} "
            f"-> "
            f"{relationship['to_table']}."
            f"{relationship['to_column']}"
        )

    return "\n".join(lines)