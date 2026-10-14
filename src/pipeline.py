
from src.inference.sql_generator import SQLGenerator
from src.database.query_executor import QueryExecutor
from src.validation.sql_validator import validate_sql


class TextToSQLPipeline:

    def __init__(
        self,
        max_attempts=3
    ):

        print("Initializing Text-to-SQL Pipeline...")

        self.generator = SQLGenerator(
            max_attempts=max_attempts
        )

        self.executor = QueryExecutor()

        self.max_attempts = max_attempts

        print("Text-to-SQL Pipeline ready.")

    # ==========================================================
    # CLEAN CORRECTION RESPONSE
    # ==========================================================

    def clean_correction_response(
        self,
        response
    ):

        if not response:
            return ""

        response = response.strip()

        # Remove markdown code fences

        response = response.replace(
            "```sql",
            ""
        )

        response = response.replace(
            "```SQL",
            ""
        )

        response = response.replace(
            "```Sql",
            ""
        )

        response = response.replace(
            "```",
            ""
        )

        response = response.strip()

        # ------------------------------------------------------
        # If the model returned an explanation before SQL,
        # start from the first SELECT.
        # ------------------------------------------------------

        select_position = (
            response.upper().find("SELECT")
        )

        if select_position != -1:

            response = response[
                select_position:
            ]

        else:

            return ""

        # ------------------------------------------------------
        # Remove common explanation sections after SQL.
        # ------------------------------------------------------

        explanation_markers = [

            "\n**Explanation**",
            "\n**EXPLANATION**",
            "\nExplanation:",
            "\nEXPLANATION:",
            "\n**Created Question**",
            "\nCreated Question:",
            "\n**Question**",
            "\nQuestion:",
            "\nHere is the corrected SQL",
            "\nHere is the SQL",
            "\nThis query",
            "\nThis SQL",
            "\nThe query",
            "\nThe corrected query",
            "\nThe corrected SQL"
        ]

        earliest_position = None

        for marker in explanation_markers:

            position = response.find(
                marker
            )

            if position != -1:

                if (
                    earliest_position is None
                    or position < earliest_position
                ):

                    earliest_position = position

        if earliest_position is not None:

            response = response[
                :earliest_position
            ]

        # ------------------------------------------------------
        # Keep only the first SQL statement.
        # ------------------------------------------------------

        semicolon_position = (
            response.find(";")
        )

        if semicolon_position != -1:

            response = response[
                :semicolon_position + 1
            ]

        return response.strip()

    # ==========================================================
    # EXECUTION ERROR CORRECTION
    # ==========================================================

    def correct_execution_error(
        self,
        question,
        sql,
        error
    ):

        print(
            "\nSending DuckDB execution error "
            "back to Qwen..."
        )

        prompt = f"""
You are an expert DuckDB SQL debugging assistant.

Your task is to fix the SQL query using the
DuckDB execution error.

USER QUESTION:

{question}

PREVIOUS SQL:

{sql}

DUCKDB EXECUTION ERROR:

{error}

DATABASE SCHEMA:

customers:
- customer_id
- customer_name
- email
- city
- state
- country
- signup_date
- customer_segment

orders:
- order_id
- customer_id
- employee_id
- order_date
- status
- sales_amount
- discount
- shipping_cost

order_items:
- order_item_id
- order_id
- product_id
- quantity
- unit_price
- discount

products:
- product_id
- product_name
- category
- subcategory
- price
- cost

employees:
- employee_id
- employee_name
- department
- city

VALID RELATIONSHIPS:

customers.customer_id = orders.customer_id

employees.employee_id = orders.employee_id

orders.order_id = order_items.order_id

products.product_id = order_items.product_id

IMPORTANT:

The previous SQL may contain a GROUP BY,
aggregation, JOIN, alias, or column error.

Fix the actual DuckDB execution error.

For ranking customers by revenue, the query
must aggregate revenue per customer.

Example structure:

SELECT
    c.customer_name,
    SUM(o.sales_amount) AS revenue
FROM customers c
JOIN orders o
    ON c.customer_id = o.customer_id
GROUP BY c.customer_name
ORDER BY revenue DESC
LIMIT 5;

Do not blindly copy this example unless it
matches the user's question.

RULES:

1. Return ONLY one SQL SELECT query.
2. Do not explain anything.
3. Do not use markdown.
4. Do not write "Explanation".
5. Do not write "Created Question".
6. Do not repeat the user question.
7. Do not describe the correction.
8. Do not add comments.
9. Use only tables from the schema.
10. Use only columns from the schema.
11. Use valid DuckDB SQL.
12. Use valid table aliases.
13. Every alias must be defined before use.
14. Use the provided relationships.
15. Do not invent columns.
16. Do not invent tables.
17. Preserve the original user intent.
18. Use GROUP BY whenever aggregation requires it.
19. Return exactly one SQL query.

CORRECTED SQL:
"""

        response = self.generator.llm.generate(
            prompt,
            max_new_tokens=256
        )

        corrected_sql = (
            self.clean_correction_response(
                response
            )
        )

        return corrected_sql

    # ==========================================================
    # VALIDATE CORRECTED SQL
    # ==========================================================

    def validate_corrected_sql(
        self,
        sql
    ):

        if not sql:

            return {
                "success": False,
                "error": (
                    "Qwen returned an empty or "
                    "non-SQL correction."
                )
            }

        valid, message = validate_sql(
            sql
        )

        if not valid:

            return {
                "success": False,
                "error": message
            }

        return {
            "success": True,
            "error": None
        }

    # ==========================================================
    # PROCESS QUESTION
    # ==========================================================

    def process(
        self,
        question
    ):

        print(
            "\n" + "=" * 70
        )

        print(
            "TEXT-TO-SQL PIPELINE"
        )

        print(
            "=" * 70
        )

        print(
            "\nUser Question:"
        )

        print(
            question
        )

        print(
            "\nGenerating SQL..."
        )

        generation_result = (
            self.generator.generate_and_validate(
                question
            )
        )

        if not generation_result[
            "success"
        ]:

            return {
                "success": False,
                "question": question,
                "sql": generation_result[
                    "sql"
                ],
                "columns": [],
                "rows": [],
                "error": generation_result[
                    "error"
                ]
            }

        sql = generation_result[
            "sql"
        ]

        # ======================================================
        # EXECUTION LOOP
        # ======================================================

        for execution_attempt in range(
            1,
            self.max_attempts + 1
        ):

            print(
                "\n" + "-" * 70
            )

            print(
                f"EXECUTION ATTEMPT "
                f"{execution_attempt}/"
                f"{self.max_attempts}"
            )

            print(
                "-" * 70
            )

            print(
                "\nExecuting SQL:"
            )

            print(
                sql
            )

            # --------------------------------------------------
            # Basic protection against non-SQL model output
            # --------------------------------------------------

            if not sql:

                error = (
                    "Generated SQL is empty."
                )

                print(
                    "\nSQL execution failed."
                )

                print(
                    error
                )

            else:

                result = (
                    self.executor.execute(
                        sql
                    )
                )

                if result[
                    "success"
                ]:

                    print(
                        "\nSQL executed successfully."
                    )

                    print(
                        "\nResults:"
                    )

                    for row in result[
                        "rows"
                    ]:

                        print(
                            row
                        )

                    return {
                        "success": True,
                        "question": question,
                        "sql": sql,
                        "columns": result[
                            "columns"
                        ],
                        "rows": result[
                            "rows"
                        ],
                        "error": None
                    }

                error = result[
                    "error"
                ]

                print(
                    "\nSQL execution failed."
                )

                print(
                    "DuckDB error:"
                )

                print(
                    error
                )

            # --------------------------------------------------
            # Stop after maximum attempts
            # --------------------------------------------------

            if execution_attempt == (
                self.max_attempts
            ):

                print(
                    "\nMaximum execution "
                    "correction attempts reached."
                )

                return {
                    "success": False,
                    "question": question,
                    "sql": sql,
                    "columns": [],
                    "rows": [],
                    "error": error
                }

            # --------------------------------------------------
            # Ask Qwen to correct the SQL
            # --------------------------------------------------

            corrected_sql = (
                self.correct_execution_error(
                    question,
                    sql,
                    error
                )
            )

            print(
                "\nQwen corrected SQL:"
            )

            print(
                "-" * 70
            )

            print(
                corrected_sql
            )

            # --------------------------------------------------
            # Validate correction before execution
            # --------------------------------------------------

            validation_result = (
                self.validate_corrected_sql(
                    corrected_sql
                )
            )

            if not validation_result[
                "success"
            ]:

                print(
                    "\nCorrected SQL failed "
                    "validation:"
                )

                print(
                    validation_result[
                        "error"
                    ]
                )

                sql = corrected_sql

                continue

            print(
                "\nCorrected SQL passed "
                "SQL validation."
            )

            sql = corrected_sql

        return {
            "success": False,
            "question": question,
            "sql": sql,
            "columns": [],
            "rows": [],
            "error": (
                "Unknown pipeline error."
            )
        }


# ==========================================================
# MAIN TEST
# ==========================================================

if __name__ == "__main__":

    pipeline = TextToSQLPipeline(
        max_attempts=3
    )

    question = (
        "Show the top 5 customers by revenue."
    )

    result = pipeline.process(
        question
    )

    print(
        "\n" + "=" * 70
    )

    print(
        "FINAL PIPELINE RESULT"
    )

    print(
        "=" * 70
    )

    print(
        "\nSuccess:"
    )

    print(
        result["success"]
    )

    print(
        "\nQuestion:"
    )

    print(
        result["question"]
    )

    print(
        "\nSQL:"
    )

    print(
        result["sql"]
    )

    print(
        "\nColumns:"
    )

    print(
        result["columns"]
    )

    print(
        "\nRows:"
    )

    for row in result[
        "rows"
    ]:

        print(
            row
        )

    if result[
        "error"
    ]:

        print(
            "\nError:"
        )

        print(
            result["error"]
        )
