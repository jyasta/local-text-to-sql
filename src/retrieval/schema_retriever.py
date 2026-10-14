from src.database.schema import get_schema
from src.database.relationships import RELATIONSHIPS


class SchemaRetriever:

    def __init__(self, top_k=3):

        self.schema = get_schema()
        self.relationships = RELATIONSHIPS
        self.top_k = top_k

        # --------------------------------------------------
        # Direct table vocabulary
        # --------------------------------------------------

        self.table_keywords = {

            "customers": {
                "customer",
                "customers",
                "client",
                "clients",
                "buyer",
                "buyers",
                "user",
                "users",
                "account",
                "accounts",
                "customer_name",
                "customer_id",
                "city",
                "state",
                "country",
                "signup",
                "signup_date",
                "segment",
                "customer_segment",
            },

            "orders": {
                "order",
                "orders",
                "sale",
                "sales",
                "revenue",
                "amount",
                "total",
                "transaction",
                "transactions",
                "purchase",
                "purchases",
                "booking",
                "bookings",
                "status",
                "discount",
                "shipping",
                "shipping_cost",
                "sales_amount",
                "order_date",
                "date",
            },

            "order_items": {
                "order_item",
                "order_items",
                "item",
                "items",
                "quantity",
                "unit_price",
                "line",
                "lines",
            },

            "products": {
                "product",
                "products",
                "goods",
                "category",
                "categories",
                "subcategory",
                "price",
                "cost",
                "product_name",
                "product_id",
                "expensive",
                "cheapest",
            },

            "employees": {
                "employee",
                "employees",
                "staff",
                "worker",
                "workers",
                "salesperson",
                "salespeople",
                "representative",
                "representatives",
                "department",
                "employee_name",
                "employee_id",
            },
        }

        # --------------------------------------------------
        # Semantic vocabulary
        # --------------------------------------------------

        self.semantic_keywords = {

            "revenue": {
                "orders",
                "sales",
                "sale",
                "income",
                "earnings",
            },

            "sales": {
                "orders",
                "revenue",
                "sale",
                "amount",
            },

            "customer": {
                "customers",
                "client",
                "clients",
                "buyer",
                "buyers",
            },

            "employee": {
                "employees",
                "staff",
                "worker",
                "workers",
                "salesperson",
                "salespeople",
                "representative",
                "representatives",
            },

            "product": {
                "products",
                "goods",
            },

            "item": {
                "order_items",
                "products",
            },

            "quantity": {
                "order_items",
                "units",
            },

            "price": {
                "products",
            },

            "cost": {
                "products",
            },

            "discount": {
                "orders",
                "order_items",
            },

            "shipping": {
                "orders",
            },

            "department": {
                "employees",
            },

            "location": {
                "customers",
                "employees",
            },
        }

        # --------------------------------------------------
        # Table dependency hints
        #
        # These describe when a second table is normally
        # required to answer a business question.
        # --------------------------------------------------

        self.join_rules = [

            {
                "required_terms": {
                    "customer",
                    "customers",
                    "client",
                    "clients",
                    "buyer",
                    "buyers",
                },
                "table": "customers",
                "related_table": "orders",
            },

            {
                "required_terms": {
                    "employee",
                    "employees",
                    "staff",
                    "worker",
                    "workers",
                    "salesperson",
                    "salespeople",
                    "representative",
                    "representatives",
                    "department",
                },
                "table": "employees",
                "related_table": "orders",
            },

            {
                "required_terms": {
                    "product",
                    "products",
                    "category",
                    "categories",
                    "subcategory",
                    "product_name",
                },
                "table": "products",
                "related_table": "order_items",
            },

            {
                "required_terms": {
                    "quantity",
                    "unit_price",
                    "order_item",
                    "order_items",
                    "items",
                },
                "table": "order_items",
                "related_table": "products",
            },
        ]

    # ==========================================================
    # TOKENIZATION
    # ==========================================================

    def tokenize(self, text):

        text = text.lower()

        tokens = set()

        for word in text.split():

            cleaned_word = word.strip(
                ".,?!:;()[]{}\"'"
            )

            if cleaned_word:
                tokens.add(
                    cleaned_word
                )

        return tokens

    # ==========================================================
    # TOKEN EXPANSION
    # ==========================================================

    def expand_tokens(
        self,
        question_tokens
    ):

        expanded_tokens = set(
            question_tokens
        )

        for token in question_tokens:

            expanded_tokens.update(
                self.semantic_keywords.get(
                    token,
                    set()
                )
            )

        return expanded_tokens

    # ==========================================================
    # SCORE TABLE
    # ==========================================================

    def score_table(
        self,
        table_name,
        question_tokens
    ):

        score = 0

        keywords = self.table_keywords.get(
            table_name,
            set()
        )

        # --------------------------------------------------
        # Direct keyword match
        # --------------------------------------------------

        for token in question_tokens:

            if token in keywords:

                score += 2

        # --------------------------------------------------
        # Semantic match
        # --------------------------------------------------

        expanded_tokens = (
            self.expand_tokens(
                question_tokens
            )
        )

        for token in expanded_tokens:

            if token in keywords:

                score += 1

        # --------------------------------------------------
        # Column matching
        # --------------------------------------------------

        if table_name in self.schema:

            for column in self.schema[
                table_name
            ]:

                column_name = (
                    column["name"].lower()
                )

                # Exact column
                if column_name in question_tokens:

                    score += 4

                # Individual words from
                # compound column names
                for part in column_name.split("_"):

                    if part in question_tokens:

                        score += 1

        # --------------------------------------------------
        # Exact table name
        # --------------------------------------------------

        if table_name in question_tokens:

            score += 5

        return score

    # ==========================================================
    # CHECK WHETHER JOIN IS NEEDED
    # ==========================================================

    def needs_related_table(
        self,
        question_tokens,
        selected_table,
        related_table
    ):

        # --------------------------------------------------
        # Business concepts that require relationships
        # --------------------------------------------------

        for rule in self.join_rules:

            if (
                rule["table"] == selected_table
                and rule["related_table"] == related_table
            ):

                if (
                    question_tokens
                    & rule["required_terms"]
                ):

                    # A second table is needed only when
                    # the question also contains a business
                    # metric that belongs to that table.
                    if related_table == "orders":

                        metric_terms = {
                            "revenue",
                            "sales",
                            "sale",
                            "amount",
                            "transaction",
                            "transactions",
                            "purchase",
                            "purchases",
                            "order",
                            "orders",
                        }

                        return bool(
                            question_tokens
                            & metric_terms
                        )

                    if related_table == "order_items":

                        item_terms = {
                            "quantity",
                            "sold",
                            "sales",
                            "units",
                            "items",
                        }

                        return bool(
                            question_tokens
                            & item_terms
                        )

                    if related_table == "products":

                        product_terms = {
                            "product",
                            "products",
                            "category",
                            "categories",
                            "price",
                            "cost",
                        }

                        return bool(
                            question_tokens
                            & product_terms
                        )

        return False

    # ==========================================================
    # GET RELATED TABLES
    # ==========================================================

    def get_related_tables(
        self,
        selected_tables,
        question_tokens
    ):

        related = []

        for relationship in self.relationships:

            from_table = (
                relationship["from_table"]
            )

            to_table = (
                relationship["to_table"]
            )

            if from_table in selected_tables:

                if to_table in selected_tables:
                    continue

                if self.needs_related_table(
                    question_tokens,
                    from_table,
                    to_table
                ):

                    related.append(
                        to_table
                    )

            if to_table in selected_tables:

                if from_table in selected_tables:
                    continue

                if self.needs_related_table(
                    question_tokens,
                    to_table,
                    from_table
                ):

                    related.append(
                        from_table
                    )

        return related

    # ==========================================================
    # RETRIEVE TABLES
    # ==========================================================

    def retrieve(
        self,
        question
    ):

        question_tokens = (
            self.tokenize(
                question
            )
        )

        scored_tables = []

        for table_name in self.schema:

            score = self.score_table(
                table_name,
                question_tokens
            )

            scored_tables.append(
                (
                    table_name,
                    score
                )
            )

        # --------------------------------------------------
        # Highest score first
        # --------------------------------------------------

        scored_tables.sort(
            key=lambda item: item[1],
            reverse=True
        )

        # --------------------------------------------------
        # Directly relevant tables
        # --------------------------------------------------

        selected_tables = [
            table
            for table, score
            in scored_tables
            if score > 0
        ]

        # --------------------------------------------------
        # Fallback
        # --------------------------------------------------

        if not selected_tables:

            return list(
                self.schema.keys()
            )

        selected_tables = (
            selected_tables[:self.top_k]
        )

        # --------------------------------------------------
        # Add related table ONLY when needed
        # --------------------------------------------------

        related_tables = (
            self.get_related_tables(
                selected_tables,
                question_tokens
            )
        )

        for table in related_tables:

            if (
                table not in selected_tables
                and len(selected_tables) < self.top_k
            ):

                selected_tables.append(
                    table
                )

        return selected_tables

    # ==========================================================
    # RELEVANT SCHEMA
    # ==========================================================

    def get_relevant_schema(
        self,
        question
    ):

        tables = self.retrieve(
            question
        )

        relevant_schema = {}

        for table_name in tables:

            if table_name in self.schema:

                relevant_schema[
                    table_name
                ] = self.schema[
                    table_name
                ]

        return relevant_schema

    # ==========================================================
    # RELEVANT RELATIONSHIPS
    # ==========================================================

    def get_relevant_relationships(
        self,
        tables
    ):

        table_set = set(
            tables
        )

        lines = []

        for relationship in self.relationships:

            from_table = (
                relationship["from_table"]
            )

            to_table = (
                relationship["to_table"]
            )

            if (
                from_table in table_set
                and to_table in table_set
            ):

                lines.append(
                    f"{from_table}."
                    f"{relationship['from_column']}"
                    f" = "
                    f"{to_table}."
                    f"{relationship['to_column']}"
                )

        return "\n".join(
            lines
        )

    # ==========================================================
    # DEBUG OUTPUT
    # ==========================================================

    def print_results(
        self,
        question
    ):

        question_tokens = (
            self.tokenize(
                question
            )
        )

        tables = self.retrieve(
            question
        )

        print("\nQuestion:")
        print(question)

        print("\nQuestion Tokens:")
        print("-" * 50)

        print(
            sorted(question_tokens)
        )

        print("\nRetrieved Tables:")
        print("-" * 50)

        for table in tables:

            print(table)

        print("\nRelevant Relationships:")
        print("-" * 50)

        relationships = (
            self.get_relevant_relationships(
                tables
            )
        )

        if relationships:

            print(
                relationships
            )

        else:

            print(
                "No relationships found."
            )

        print("\nTable Scores:")
        print("-" * 50)

        for table_name in self.schema:

            score = self.score_table(
                table_name,
                question_tokens
            )

            print(
                f"{table_name:<20} "
                f"{score}"
            )


# ==========================================================
# TEST
# ==========================================================

if __name__ == "__main__":

    retriever = SchemaRetriever(
        top_k=3
    )

    test_questions = [

        "Show the top 5 customers by revenue.",

        "Which staff members generated the highest sales?",

        "Show the most expensive products.",

        "What is the total quantity sold?",

        "Show sales by department.",

        "Show product sales by category.",
    ]

    for question in test_questions:

        print(
            "\n" + "=" * 70
        )

        retriever.print_results(
            question
        )