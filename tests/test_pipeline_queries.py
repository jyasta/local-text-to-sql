from src.pipeline import TextToSQLPipeline


def main():

    pipeline = TextToSQLPipeline(
        max_attempts=3
    )

    questions = [

        "Show the top 10 customers by revenue.",

        "What is the average order value?",

        "Show total sales by department.",

        "Which products have the highest quantity sold?",

        "Show revenue for orders placed in 2025.",

        "Show the top 5 product categories by sales.",
    ]

    for index, question in enumerate(
        questions,
        start=1
    ):

        print(
            "\n\n"
            + "#" * 80
        )

        print(
            f"TEST {index}"
        )

        print(
            "#" * 80
        )

        result = pipeline.process(
            question
        )

        print(
            "\nFINAL STATUS:"
        )

        print(
            "Success:",
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

        for row in result["rows"]:

            print(row)

        if result["error"]:

            print(
                "\nError:"
            )

            print(
                result["error"]
            )


if __name__ == "__main__":

    main()