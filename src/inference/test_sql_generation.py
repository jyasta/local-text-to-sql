from src.database.schema import get_schema
from src.inference.prompt import build_sql_prompt
from src.inference.llm import LocalLLM


def main():

    question = "Show the top 5 customers by revenue."

    # Get database schema
    schema = get_schema()

    # Build schema-aware prompt
    prompt = build_sql_prompt(
        question,
        schema
    )

    # Load local Qwen model
    llm = LocalLLM()

    # Generate SQL
    sql = llm.generate(
        prompt,
        max_new_tokens=256
    )

    print("\nGenerated SQL")
    print("=" * 60)
    print(sql)


if __name__ == "__main__":
    main()