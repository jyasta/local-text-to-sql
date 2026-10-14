import re


METRICS = {

    "revenue": {
        "expression": "SUM(o.sales_amount)",
        "tables": ["orders"],
        "description": (
            "Total revenue from orders using "
            "orders.sales_amount."
        ),
    },

    "order_value": {
        "expression": "o.sales_amount",
        "tables": ["orders"],
        "description": (
            "Value of an individual order. "
            "Average order value must use AVG(o.sales_amount) "
            "from the orders table without joining order_items."
        ),
    },

    "sales": {
        "expression": "SUM(o.sales_amount)",
        "tables": ["orders"],
        "description": (
            "Total sales from orders using "
            "orders.sales_amount."
        ),
    },

    "quantity_sold": {
        "expression": "SUM(oi.quantity)",
        "tables": ["order_items"],
        "description": (
            "Total quantity of products sold using "
            "order_items.quantity."
        ),
    },

    "product_sales": {
        "expression": "SUM(oi.quantity * oi.unit_price)",
        "tables": [
            "order_items",
            "products"
        ],
        "grouping_columns": [
            "products.product_name",
            "products.category",
            "products.subcategory"
        ],
        "description": (
            "Sales value attributed to products or product "
            "categories using order item quantity and unit price. "
            "Products must be joined through "
            "order_items.product_id = products.product_id."
        ),
    },

    "profit": {
        "expression": (
            "SUM(oi.quantity * "
            "(oi.unit_price - p.cost))"
        ),
        "tables": [
            "order_items",
            "products"
        ],
        "grouping_columns": [
            "products.product_name",
            "products.category",
            "products.subcategory"
        ],
        "description": (
            "Estimated product profit calculated from "
            "quantity multiplied by unit price minus product cost."
        ),
    },
}


ALIASES = {

    "revenue": [
        "total revenue",
        "customer revenue",
        "revenue",
        "earnings",
        "income"
    ],

    "order_value": [
        "average order value",
        "aov",
        "order value",
        "average order"
    ],

    "quantity_sold": [
        "quantity sold",
        "units sold",
        "number of units",
        "quantity"
    ],

    "product_sales": [
        "product category sales",
        "product sales",
        "sales by category",
        "sales by product",
        "sales by subcategory",
        "category sales",
        "product revenue",
        "category revenue"
    ],

    "profit": [
        "total profit",
        "profit by product",
        "profit by category",
        "profit margin",
        "profit"
    ],

    "sales": [
        "total sales",
        "sales amount",
        "sales value",
        "sales"
    ],
}


GROUPING_RULES = {

    "customer": {
        "keywords": [
            "customer",
            "customers",
            "client",
            "clients"
        ],
        "column": "c.customer_name",
        "table": "customers",
        "description": "Group results by customer name.",
    },

    "product": {
        "keywords": [
            "product",
            "products"
        ],
        "column": "p.product_name",
        "table": "products",
        "description": "Group results by product name.",
    },

    "category": {
        "keywords": [
            "category",
            "categories"
        ],
        "column": "p.category",
        "table": "products",
        "description": "Group results by product category.",
    },

    "subcategory": {
        "keywords": [
            "subcategory",
            "subcategories"
        ],
        "column": "p.subcategory",
        "table": "products",
        "description": "Group results by product subcategory.",
    },

    "department": {
        "keywords": [
            "department",
            "departments"
        ],
        "column": "e.department",
        "table": "employees",
        "description": "Group results by employee department.",
    },

    "city": {
        "keywords": [
            "city",
            "cities"
        ],
        "column": "c.city",
        "table": "customers",
        "description": "Group results by customer city.",
    },

    "state": {
        "keywords": [
            "state",
            "states"
        ],
        "column": "c.state",
        "table": "customers",
        "description": "Group results by customer state.",
    },
}


def normalize_question(question):
    return re.sub(
        r"\s+",
        " ",
        question.strip().lower()
    )


def find_metrics(question):
    question = normalize_question(question)

    # Product/category/subcategory sales must be detected
    # before the generic "sales" metric.
    if (
        (
            "product" in question
            or "category" in question
            or "categories" in question
            or "subcategory" in question
            or "subcategories" in question
        )
        and (
            "sales" in question
            or "revenue" in question
        )
    ):
        return "product_sales"

    # Product/category profit is product-level profit.
    if (
        (
            "product" in question
            or "category" in question
            or "subcategory" in question
        )
        and "profit" in question
    ):
        return "profit"

    priority_order = [
        "order_value",
        "quantity_sold",
        "profit",
        "revenue",
        "sales",
    ]

    for metric_name in priority_order:

        aliases = ALIASES[metric_name]

        for alias in sorted(
            aliases,
            key=len,
            reverse=True
        ):

            if alias in question:
                return metric_name

    return None


def find_grouping(question):
    question = normalize_question(question)

    priority_order = [
        "subcategory",
        "category",
        "product",
        "customer",
        "department",
        "state",
        "city",
    ]

    for grouping_name in priority_order:

        rule = GROUPING_RULES[grouping_name]

        for keyword in rule["keywords"]:

            if re.search(
                rf"\b{re.escape(keyword)}\b",
                question
            ):
                return grouping_name

    return None


def find_limit(question):
    question = normalize_question(question)

    patterns = [
        r"\btop\s+(\d+)\b",
        r"\bfirst\s+(\d+)\b",
        r"\bhighest\s+(\d+)\b",
        r"\blargest\s+(\d+)\b",
        r"\bbest\s+(\d+)\b",
        r"\bbottom\s+(\d+)\b",
        r"\blast\s+(\d+)\b",
        r"\blowest\s+(\d+)\b",
        r"\bsmallest\s+(\d+)\b",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            question
        )

        if match:
            return int(match.group(1))

    singular_patterns = [
        r"\bhighest\b",
        r"\blargest\b",
        r"\bbest\b",
        r"\blowest\b",
        r"\bsmallest\b",
    ]

    for pattern in singular_patterns:

        if re.search(pattern, question):
            return 1

    return None


def find_sort_direction(question):
    question = normalize_question(question)

    ascending_keywords = [
        "bottom",
        "lowest",
        "smallest",
        "least"
    ]

    descending_keywords = [
        "top",
        "highest",
        "largest",
        "best",
        "most"
    ]

    for keyword in ascending_keywords:

        if re.search(
            rf"\b{re.escape(keyword)}\b",
            question
        ):
            return "ASC"

    for keyword in descending_keywords:

        if re.search(
            rf"\b{re.escape(keyword)}\b",
            question
        ):
            return "DESC"

    return None


def find_year(question):
    question = normalize_question(question)

    match = re.search(
        r"\b(20\d{2})\b",
        question
    )

    if match:
        return int(match.group(1))

    return None


def find_date_filter(question):
    year = find_year(question)

    if year is None:
        return None

    return {
        "year": year,
        "start": f"{year}-01-01",
        "end": f"{year + 1}-01-01",
        "description": (
            f"Orders placed from {year}-01-01 "
            f"through {year}-12-31."
        ),
    }


def find_aggregation(question, metric=None):
    question = normalize_question(question)

    # "highest quantity sold" means:
    #
    # SUM(quantity) for each product
    # ORDER BY SUM(quantity) DESC
    #
    # It does NOT mean MAX(quantity).

    if metric == "quantity_sold":
        return "SUM"

    if metric == "product_sales":
        return "SUM"

    if metric == "profit":
        return "SUM"

    if metric == "revenue":
        return "SUM"

    if metric == "sales":
        return "SUM"

    if metric == "order_value":
        return "AVG"

    if (
        "average" in question
        or "avg" in question
        or "mean" in question
    ):
        return "AVG"

    if (
        "count" in question
        or "number of" in question
        or "how many" in question
    ):
        return "COUNT"

    if (
        "maximum" in question
        or re.search(r"\bmax\b", question)
    ):
        return "MAX"

    if (
        "minimum" in question
        or re.search(r"\bmin\b", question)
    ):
        return "MIN"

    return None


def get_required_tables(metric, grouping=None):
    if metric not in METRICS:
        return []

    tables = list(
        METRICS[metric].get(
            "tables",
            []
        )
    )

    if grouping in GROUPING_RULES:

        grouping_table = GROUPING_RULES[
            grouping
        ]["table"]

        if grouping_table not in tables:
            tables.append(grouping_table)

    return tables


def get_output_columns(metric, grouping=None):
    output = []

    if grouping in GROUPING_RULES:

        output.append(
            GROUPING_RULES[grouping]["column"]
        )

    if metric == "order_value":

        output.append(
            "AVG(o.sales_amount)"
        )

    elif metric in METRICS:

        output.append(
            METRICS[metric]["expression"]
        )

    return output


def get_query_intent(question):
    normalized = normalize_question(
        question
    )

    metric = find_metrics(
        normalized
    )

    grouping = find_grouping(
        normalized
    )

    aggregation = find_aggregation(
        normalized,
        metric
    )

    limit = find_limit(
        normalized
    )

    sort_direction = find_sort_direction(
        normalized
    )

    year = find_year(
        normalized
    )

    date_filter = find_date_filter(
        normalized
    )

    required_tables = get_required_tables(
        metric,
        grouping
    )

    output_columns = get_output_columns(
        metric,
        grouping
    )

    return {
        "question": question,
        "metric": metric,
        "metric_definition": (
            METRICS[metric]
            if metric in METRICS
            else None
        ),
        "aggregation": aggregation,
        "grouping": grouping,
        "grouping_definition": (
            GROUPING_RULES[grouping]
            if grouping in GROUPING_RULES
            else None
        ),
        "limit": limit,
        "sort_direction": sort_direction,
        "year": year,
        "date_filter": date_filter,
        "required_tables": required_tables,
        "output_columns": output_columns,
    }


def format_query_intent(intent):
    lines = []

    lines.append(
        f"Metric: {intent['metric'] or 'Not detected'}"
    )

    lines.append(
        f"Aggregation: "
        f"{intent['aggregation'] or 'Not detected'}"
    )

    lines.append(
        f"Grouping: "
        f"{intent['grouping'] or 'None'}"
    )

    lines.append(
        f"Limit: "
        f"{intent['limit'] if intent['limit'] is not None else 'None'}"
    )

    lines.append(
        f"Sort direction: "
        f"{intent['sort_direction'] or 'Not specified'}"
    )

    if intent["date_filter"]:

        date_filter = intent["date_filter"]

        lines.append(
            f"Date range: "
            f"{date_filter['start']} <= order_date < "
            f"{date_filter['end']}"
        )

    else:

        lines.append(
            "Date range: None"
        )

    lines.append(
        "Required tables: "
        + (
            ", ".join(
                intent["required_tables"]
            )
            if intent["required_tables"]
            else "Not detected"
        )
    )

    if intent["output_columns"]:

        lines.append(
            "Expected output expressions: "
            + ", ".join(
                intent["output_columns"]
            )
        )

    if intent["metric_definition"]:

        lines.append(
            "Metric meaning: "
            + intent["metric_definition"][
                "description"
            ]
        )

    if intent["grouping_definition"]:

        lines.append(
            "Grouping meaning: "
            + intent["grouping_definition"][
                "description"
            ]
        )

    return "\n".join(lines)


if __name__ == "__main__":

    test_questions = [
        "Show the top 10 customers by revenue.",
        "What is the average order value?",
        "Show total sales by department.",
        "Which products have the highest quantity sold?",
        "Show revenue for orders placed in 2025.",
        "Show the top 5 product categories by sales.",
    ]

    print("\nSEMANTIC INTENT TEST")
    print("=" * 80)

    for index, question in enumerate(
        test_questions,
        start=1
    ):

        print(
            f"\nTEST {index}: {question}"
        )
        print("-" * 80)

        intent = get_query_intent(
            question
        )

        print(
            format_query_intent(
                intent
            )
        )