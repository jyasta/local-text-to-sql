def build_sql_prompt(question, schema):
    schema_text = []

    for table_name, columns in schema.items():
        schema_text.append(f"Table: {table_name}")

        for column in columns:
            schema_text.append(
                f"  - {column['name']} ({column['type']})"
            )

        schema_text.append("")

    schema_text = "\n".join(schema_text)

    prompt = f"""
You are an expert SQL generation assistant.

Your task is to convert a natural language question into
valid DuckDB SQL.

DATABASE SCHEMA:
{schema_text}

RULES:
- Use only tables and columns from the provided schema.
- Generate valid DuckDB SQL.
- Do not invent tables or columns.
- Return only the SQL query.
- Do not include markdown.
- Do not explain the query.

USER QUESTION:
{question}

SQL:
"""

    return prompt