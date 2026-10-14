from src.database.schema import get_schema
from src.inference.prompt import build_sql_prompt


def main():

    schema = get_schema()

    question = "Show the top 5 customers by revenue."

    prompt = build_sql_prompt(
        question,
        schema
    )

    print(prompt)


if __name__ == "__main__":
    main()