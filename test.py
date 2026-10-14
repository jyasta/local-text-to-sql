from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

MODEL_NAME = "Qwen/Qwen2.5-Coder-0.5B-Instruct"

print("Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

print("Loading model...")
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    torch_dtype=torch.float32
)

print("Model loaded successfully!")
print("Device:", next(model.parameters()).device)

prompt = """### Instruction
Generate SQL for the user's question.

### Database Schema
CUSTOMERS(
    customer_id,
    customer_name,
    city
)

ORDERS(
    order_id,
    customer_id,
    amount
)

### Question
Show the top 5 customers by revenue.

### SQL
"""

inputs = tokenizer(prompt, return_tensors="pt")

print("Generating SQL...")

with torch.no_grad():
    outputs = model.generate(
        **inputs,
        max_new_tokens=100,
        temperature=0.1,
        do_sample=False
    )

result = tokenizer.decode(outputs[0], skip_special_tokens=True)

print("\n========== MODEL OUTPUT ==========")
print(result)
print("==================================")