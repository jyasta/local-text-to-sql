from transformers import AutoTokenizer, AutoModelForCausalLM
import torch


MODEL_NAME = "Qwen/Qwen2.5-Coder-0.5B-Instruct"


class LocalLLM:

    def __init__(self):

        print("Loading local Qwen model...")

        # --------------------------------------------------
        # Tokenizer
        # --------------------------------------------------

        self.tokenizer = (
            AutoTokenizer.from_pretrained(
                MODEL_NAME
            )
        )

        # --------------------------------------------------
        # Model
        # --------------------------------------------------

        self.model = (
            AutoModelForCausalLM.from_pretrained(
                MODEL_NAME,
                dtype=torch.float32
            )
        )

        # --------------------------------------------------
        # Disable sampling parameters
        #
        # We use deterministic generation.
        # Therefore temperature/top_p/top_k are unnecessary.
        # --------------------------------------------------

        self.model.generation_config.temperature = None
        self.model.generation_config.top_p = None
        self.model.generation_config.top_k = None

        self.model.eval()

        print(
            "Qwen model loaded successfully."
        )

        print("Device: CPU")

    # ==========================================================
    # GENERATE
    # ==========================================================

    def generate(
        self,
        prompt,
        max_new_tokens=256
    ):

        # --------------------------------------------------
        # Tokenize
        # --------------------------------------------------

        inputs = self.tokenizer(
            prompt,
            return_tensors="pt"
        )

        # --------------------------------------------------
        # Deterministic generation
        # --------------------------------------------------

        with torch.no_grad():

            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False
            )

        # --------------------------------------------------
        # Extract newly generated tokens only
        # --------------------------------------------------

        generated_tokens = (
            outputs[0][
                inputs["input_ids"].shape[1]:
            ]
        )

        # --------------------------------------------------
        # Decode
        # --------------------------------------------------

        response = (
            self.tokenizer.decode(
                generated_tokens,
                skip_special_tokens=True
            )
        )

        return response.strip()


# ==========================================================
# TEST
# ==========================================================

if __name__ == "__main__":

    llm = LocalLLM()

    prompt = """
You are an expert DuckDB SQL generation assistant.

DATABASE SCHEMA:

Table: customers
- customer_id
- customer_name
- email
- city
- state
- country
- signup_date
- customer_segment

Table: orders
- order_id
- customer_id
- employee_id
- order_date
- status
- sales_amount
- discount
- shipping_cost

RELATIONSHIP:

customers.customer_id = orders.customer_id

QUESTION:

Show the top 5 customers by revenue.

RULES:

- Use only the provided tables.
- Use only the provided columns.
- Revenue must be calculated using orders.sales_amount.
- Join customers and orders using customer_id.
- Return only SQL.
- Do not explain.
- Do not use markdown.

SQL:
"""

    result = llm.generate(
        prompt,
        max_new_tokens=256
    )

    print(
        "\nGenerated SQL:"
    )

    print("-" * 50)

    print(result)