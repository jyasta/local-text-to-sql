
from src.retrieval.schema_retriever import SchemaRetriever
from src.inference.llm import LocalLLM
from src.validation.sql_validator import validate_sql
from src.semantics.metrics import (
    get_query_intent,
    format_query_intent
)

import sqlglot
from sqlglot import exp


class SQLGenerator:

    def __init__(self, max_attempts=3):

        print("Initializing SQL Generator...")

        self.retriever = SchemaRetriever(top_k=3)
        self.llm = LocalLLM()

        self.max_attempts = max_attempts

        print("SQL Generator ready.")

    # ==========================================================
    # BUILD SCHEMA TEXT
    # ==========================================================

    def build_schema_text(self, schema):

        lines = []

        for table_name, columns in schema.items():

            lines.append(
                f"Table: {table_name}"
            )

            for column in columns:

                column_name = column["name"]
                column_type = column["type"]

                line = (
                    f"- {column_name} "
                    f"({column_type})"
                )

                values = column.get("values")

                if values:

                    formatted_values = ", ".join(
                        f"'{str(value)}'"
                        for value in values
                    )

                    line += (
                        "\n  Allowed values: "
                        f"{formatted_values}"
                    )

                lines.append(line)

            lines.append("")

        return "\n".join(lines)

    # ==========================================================
    # CLEAN SQL
    # ==========================================================

    def clean_sql(self, sql):

        if not sql:
            return ""

        sql = sql.strip()

        for marker in [
            "```sql",
            "```SQL",
            "```Sql",
            "```"
        ]:
            sql = sql.replace(marker, "")

        sql = sql.strip()

        select_position = sql.upper().find("SELECT")

        if select_position == -1:
            return sql

        sql = sql[select_position:]

        explanation_markers = [
            "\nEXPLAIN:",
            "\nExplain:",
            "\nEXPLANATION:",
            "\nExplanation:",
            "\nThis query",
            "\nThis SQL",
            "\nThe query",
            "\nThis corrected SQL",
            "\nThe corrected SQL",
            "\nHere is",
            "\nHere’s",
            "\nThis statement",
            "\nThe SQL"
        ]

        earliest_position = None

        for marker in explanation_markers:

            position = sql.find(marker)

            if position != -1:

                if (
                    earliest_position is None
                    or position < earliest_position
                ):
                    earliest_position = position

        if earliest_position is not None:
            sql = sql[:earliest_position]

        semicolon_position = sql.find(";")

        if semicolon_position != -1:
            sql = sql[:semicolon_position + 1]

        return sql.strip()

    # ==========================================================
    # REPAIR ALIASES
    # ==========================================================

    def repair_aliases(self, sql):

        if not sql:
            return sql

        try:

            expression = sqlglot.parse_one(
                sql,
                dialect="duckdb"
            )

        except Exception:

            return sql

        alias_to_table = {}

        for table in expression.find_all(exp.Table):

            table_name = table.name.lower()
            alias = table.alias_or_name.lower()

            alias_to_table[alias] = table_name

        schema = self.retriever.schema

        normalized_schema = {}

        for table_name, columns in schema.items():

            normalized_schema[
                table_name.lower()
            ] = {
                column["name"].lower()
                for column in columns
            }

        repairs = []

        for column in expression.find_all(exp.Column):

            if not column.table:
                continue

            alias = column.table.lower()
            column_name = column.name.lower()

            if alias not in alias_to_table:
                continue

            real_table = alias_to_table[alias]

            table_columns = normalized_schema.get(
                real_table,
                set()
            )

            if column_name in table_columns:
                continue

            possible_aliases = []

            for (
                candidate_alias,
                candidate_table
            ) in alias_to_table.items():

                candidate_columns = normalized_schema.get(
                    candidate_table,
                    set()
                )

                if column_name in candidate_columns:
                    possible_aliases.append(
                        candidate_alias
                    )

            if len(possible_aliases) == 1:

                correct_alias = possible_aliases[0]

                print(
                    "\nAutomatic alias repair:"
                )

                print(
                    f"  {alias}.{column.name}"
                    f" -> "
                    f"{correct_alias}.{column.name}"
                )

                column.set(
                    "table",
                    exp.to_identifier(correct_alias)
                )

                repairs.append(True)

        if not repairs:
            return sql

        try:

            return expression.sql(
                dialect="duckdb"
            ).strip()

        except Exception:

            return sql

    # ==========================================================
    # GET CONTEXT
    # ==========================================================

    def get_context(self, question):

        tables = self.retriever.retrieve(question)

        schema = self.retriever.get_relevant_schema(
            question
        )

        relationship_text = (
            self.retriever.get_relevant_relationships(
                tables
            )
        )

        query_intent = get_query_intent(
            question
        )

        semantic_context = format_query_intent(
            query_intent
        )

        return (
            tables,
            schema,
            relationship_text,
            query_intent,
            semantic_context
        )

    # ==========================================================
    # BUILD PROMPT
    # ==========================================================

    def build_prompt(
        self,
        question,
        schema_text,
        relationship_text,
        semantic_context
    ):

        return f"""
You are an expert DuckDB SQL generator.

Convert the user's natural language question
into ONE valid DuckDB SQL SELECT query.

DATABASE SCHEMA:

{schema_text}

RELATIONSHIPS:

{relationship_text}

DETERMINISTIC QUERY INTENT:

{semantic_context}

USER QUESTION:

{question}

The deterministic query intent is authoritative.

Preserve exactly:

- metric
- aggregation
- grouping
- limit
- sort direction
- date filter

Revenue:
SUM(o.sales_amount)

Average order value:
AVG(o.sales_amount)

Quantity sold:
SUM(oi.quantity)

Product/category sales:
SUM(oi.quantity * oi.unit_price)

Product/category joins must use:

p.product_id = oi.product_id

Orders and customers must use:

c.customer_id = o.customer_id

Employees and orders must use:

e.employee_id = o.employee_id

If a grouping is specified,
include the grouping column in SELECT and GROUP BY.

If sort_direction is DESC or ASC,
use:

ORDER BY metric_alias DESC

or:

ORDER BY metric_alias ASC

If a date_filter exists, use its exact start
and end dates as a half-open range:

o.order_date >= 'START'
AND o.order_date < 'END'

If a LIMIT exists, preserve it exactly.

Return ONLY SQL.

Do not explain the SQL.
Do not use markdown.
Do not return multiple statements.
Do not invent tables or columns.

Generate the SQL now.
"""

    # ==========================================================
    # DATE FILTER
    # ==========================================================

    def get_date_filter(self, query_intent):

        date_filter = query_intent.get(
            "date_filter"
        )

        if not date_filter:
            return None, None

        start = date_filter.get("start")
        end = date_filter.get("end")

        return start, end

    # ==========================================================
    # DETERMINISTIC FALLBACK
    # ==========================================================

    def build_fallback_sql(self, query_intent):

        metric = query_intent.get("metric")

        grouping = query_intent.get("grouping")

        limit = query_intent.get("limit")

        sort_direction = query_intent.get(
            "sort_direction"
        )

        date_start, date_end = (
            self.get_date_filter(
                query_intent
            )
        )

        # ======================================================
        # REVENUE
        # ======================================================

        if metric == "revenue":

            if grouping == "customer":

                sql = """
SELECT
    c.customer_name,
    SUM(o.sales_amount) AS revenue
FROM customers c
JOIN orders o
    ON c.customer_id = o.customer_id
"""

                if date_start and date_end:

                    sql += f"""
WHERE
    o.order_date >= '{date_start}'
    AND o.order_date < '{date_end}'
"""

                sql += """
GROUP BY c.customer_name
"""

                if sort_direction:

                    sql += f"""
ORDER BY revenue {sort_direction}
"""

                if limit:

                    sql += f"""
LIMIT {int(limit)}
"""

                return sql.strip() + ";"

            sql = """
SELECT
    SUM(o.sales_amount) AS revenue
FROM orders o
"""

            if date_start and date_end:

                sql += f"""
WHERE
    o.order_date >= '{date_start}'
    AND o.order_date < '{date_end}'
"""

            return sql.strip() + ";"

        # ======================================================
        # SALES
        # ======================================================

        if metric == "sales":

            if grouping == "department":

                sql = """
SELECT
    e.department,
    SUM(o.sales_amount) AS total_sales
FROM employees e
JOIN orders o
    ON e.employee_id = o.employee_id
GROUP BY e.department
"""

                if sort_direction:

                    sql += f"""
ORDER BY total_sales {sort_direction}
"""

                if limit:

                    sql += f"""
LIMIT {int(limit)}
"""

                return sql.strip() + ";"

            sql = """
SELECT
    SUM(o.sales_amount) AS total_sales
FROM orders o
"""

            if date_start and date_end:

                sql += f"""
WHERE
    o.order_date >= '{date_start}'
    AND o.order_date < '{date_end}'
"""

            return sql.strip() + ";"

        # ======================================================
        # AVERAGE ORDER VALUE
        # ======================================================

        if metric == "order_value":

            sql = """
SELECT
    AVG(o.sales_amount) AS average_order_value
FROM orders o
"""

            if date_start and date_end:

                sql += f"""
WHERE
    o.order_date >= '{date_start}'
    AND o.order_date < '{date_end}'
"""

            return sql.strip() + ";"

        # ======================================================
        # QUANTITY SOLD
        # ======================================================

        if metric == "quantity_sold":

            if grouping == "product":

                sql = """
SELECT
    p.product_name,
    SUM(oi.quantity) AS quantity_sold
FROM products p
JOIN order_items oi
    ON p.product_id = oi.product_id
GROUP BY p.product_name
"""

                if sort_direction:

                    sql += f"""
ORDER BY quantity_sold {sort_direction}
"""

                if limit:

                    sql += f"""
LIMIT {int(limit)}
"""

                return sql.strip() + ";"

        # ======================================================
        # PRODUCT SALES
        # ======================================================

        if metric == "product_sales":

            if grouping == "category":

                sql = """
SELECT
    p.category,
    SUM(oi.quantity * oi.unit_price) AS product_sales
FROM products p
JOIN order_items oi
    ON p.product_id = oi.product_id
GROUP BY p.category
"""

                if sort_direction:

                    sql += f"""
ORDER BY product_sales {sort_direction}
"""

                if limit:

                    sql += f"""
LIMIT {int(limit)}
"""

                return sql.strip() + ";"

            if grouping == "product":

                sql = """
SELECT
    p.product_name,
    SUM(oi.quantity * oi.unit_price) AS product_sales
FROM products p
JOIN order_items oi
    ON p.product_id = oi.product_id
GROUP BY p.product_name
"""

                if sort_direction:

                    sql += f"""
ORDER BY product_sales {sort_direction}
"""

                if limit:

                    sql += f"""
LIMIT {int(limit)}
"""

                return sql.strip() + ";"

            if grouping == "subcategory":

                sql = """
SELECT
    p.subcategory,
    SUM(oi.quantity * oi.unit_price) AS product_sales
FROM products p
JOIN order_items oi
    ON p.product_id = oi.product_id
GROUP BY p.subcategory
"""

                if sort_direction:

                    sql += f"""
ORDER BY product_sales {sort_direction}
"""

                if limit:

                    sql += f"""
LIMIT {int(limit)}
"""

                return sql.strip() + ";"

        # ======================================================
        # PROFIT
        # ======================================================

        if metric == "profit":

            if grouping == "category":

                sql = """
SELECT
    p.category,
    SUM(
        oi.quantity *
        (oi.unit_price - p.cost)
    ) AS profit
FROM products p
JOIN order_items oi
    ON p.product_id = oi.product_id
GROUP BY p.category
"""

                if sort_direction:

                    sql += f"""
ORDER BY profit {sort_direction}
"""

                if limit:

                    sql += f"""
LIMIT {int(limit)}
"""

                return sql.strip() + ";"

        return ""

    # ==========================================================
    # GENERATE WITH RETRY
    # ==========================================================

    def generate_with_retry(
        self,
        prompt,
        query_intent
    ):

        for attempt in range(1, 3):

            print(
                f"\nQwen generation attempt "
                f"{attempt}/2"
            )

            sql = self.llm.generate(
                prompt,
                max_new_tokens=256
            )

            sql = self.clean_sql(sql)

            if sql:

                print(
                    "\nQwen returned SQL."
                )

                return self.repair_aliases(
                    sql
                )

            print(
                "\nQwen returned empty output."
            )

        print(
            "\nQwen generation failed."
        )

        print(
            "Using deterministic semantic fallback..."
        )

        return self.build_fallback_sql(
            query_intent
        )

    # ==========================================================
    # GENERATE SQL
    # ==========================================================

    def generate_sql(self, question):

        print(
            "\nRetrieving relevant schema..."
        )

        (
            tables,
            schema,
            relationship_text,
            query_intent,
            semantic_context
        ) = self.get_context(
            question
        )

        print(
            "\nRetrieved Tables:"
        )

        print("-" * 60)

        for table in tables:
            print(table)

        schema_text = self.build_schema_text(
            schema
        )

        print(
            "\nRelevant Schema:"
        )

        print("-" * 60)

        print(schema_text)

        print(
            "\nRelevant Relationships:"
        )

        print("-" * 60)

        if relationship_text:
            print(relationship_text)
        else:
            print("No relationships found.")

        print(
            "\nDeterministic Query Intent:"
        )

        print("-" * 60)

        print(semantic_context)

        prompt = self.build_prompt(
            question,
            schema_text,
            relationship_text,
            semantic_context
        )

        print(
            "\nSending prompt to Qwen..."
        )

        sql = self.generate_with_retry(
            prompt,
            query_intent
        )

        sql = self.clean_sql(sql)

        sql = self.repair_aliases(sql)

        print(
            "\nGenerated SQL:"
        )

        print("-" * 60)

        print(sql)

        return sql

    # ==========================================================
    # CORRECTION PROMPT
    # ==========================================================

    def build_correction_prompt(
        self,
        question,
        sql,
        error,
        schema_text,
        relationship_text,
        semantic_context
    ):

        return f"""
Fix this DuckDB SQL query.

QUESTION:
{question}

SQL:
{sql}

ERROR:
{error}

SCHEMA:
{schema_text}

RELATIONSHIPS:
{relationship_text}

QUERY INTENT:
{semantic_context}

Preserve the exact:

- metric
- aggregation
- grouping
- limit
- sort direction
- date filter

Return ONLY one corrected SELECT query.

No explanation.
No markdown.
"""

    # ==========================================================
    # CORRECT SQL
    # ==========================================================

    def correct_sql(
        self,
        question,
        sql,
        error
    ):

        print(
            "\nSQL validation failed."
        )

        print("Error:")
        print(error)

        (
            tables,
            schema,
            relationship_text,
            query_intent,
            semantic_context
        ) = self.get_context(
            question
        )

        schema_text = self.build_schema_text(
            schema
        )

        prompt = self.build_correction_prompt(
            question,
            sql,
            error,
            schema_text,
            relationship_text,
            semantic_context
        )

        print(
            "\nSending correction request to Qwen..."
        )

        corrected_sql = self.llm.generate(
            prompt,
            max_new_tokens=256
        )

        corrected_sql = self.clean_sql(
            corrected_sql
        )

        corrected_sql = self.repair_aliases(
            corrected_sql
        )

        if not corrected_sql:

            print(
                "\nQwen returned empty correction."
            )

            print(
                "Using deterministic fallback."
            )

            corrected_sql = (
                self.build_fallback_sql(
                    query_intent
                )
            )

        print(
            "\nCorrected SQL:"
        )

        print("-" * 60)

        print(corrected_sql)

        return corrected_sql

    # ==========================================================
    # GENERATE AND VALIDATE
    # ==========================================================

    def generate_and_validate(
        self,
        question
    ):

        sql = self.generate_sql(
            question
        )

        for attempt in range(
            1,
            self.max_attempts + 1
        ):

            print(
                f"\nValidation attempt "
                f"{attempt}/"
                f"{self.max_attempts}"
            )

            valid, message = validate_sql(
                sql
            )

            if valid:

                print(
                    "\nSQL validation successful."
                )

                return {
                    "success": True,
                    "sql": sql,
                    "error": None
                }

            print(
                "\nValidation failed:"
            )

            print(message)

            if attempt == self.max_attempts:

                return {
                    "success": False,
                    "sql": sql,
                    "error": message
                }

            sql = self.correct_sql(
                question,
                sql,
                message
            )

        return {
            "success": False,
            "sql": sql,
            "error": "SQL validation failed."
        }


# ==========================================================
# MAIN TEST
# ==========================================================

if __name__ == "__main__":

    generator = SQLGenerator(
        max_attempts=3
    )

    question = (
        "Show the top 5 product categories by sales."
    )

    result = generator.generate_and_validate(
        question
    )

    print("\n")
    print("=" * 70)
    print("FINAL RESULT")
    print("=" * 70)

    print("\nSuccess:")
    print(result["success"])

    print("\nSQL:")
    print(result["sql"])

    print("\nError:")
    print(result["error"])
