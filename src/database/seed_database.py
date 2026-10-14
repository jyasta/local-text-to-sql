
import duckdb
import random
from datetime import date, timedelta
from pathlib import Path

DB_PATH = Path("data/database/analytics.duckdb")
random.seed(42)

CITIES = [
    "Hyderabad", "Bangalore", "Chennai", "Mumbai", "Delhi",
    "Pune", "Kolkata", "Ahmedabad", "Jaipur", "Kochi",
]

STATES = {
    "Hyderabad": "Telangana",
    "Bangalore": "Karnataka",
    "Chennai": "Tamil Nadu",
    "Mumbai": "Maharashtra",
    "Delhi": "Delhi",
    "Pune": "Maharashtra",
    "Kolkata": "West Bengal",
    "Ahmedabad": "Gujarat",
    "Jaipur": "Rajasthan",
    "Kochi": "Kerala",
}

CATEGORIES = {
    "Electronics": ["Laptop", "Monitor", "Keyboard", "Mouse", "Headphones"],
    "Home": ["Chair", "Desk", "Lamp", "Table", "Bookshelf"],
    "Mobile": ["Smartphone", "Tablet", "Smartwatch", "Charger", "Power Bank"],
    "Accessories": ["Backpack", "USB Cable", "Webcam", "Mouse Pad", "Adapter"],
    "Office": ["Notebook", "Printer", "Paper", "Pen Set", "Calculator"],
}

FIRST_NAMES = [
    "Rahul", "Priya", "Arjun", "Sneha", "Amit",
    "Ananya", "Rohit", "Kavya", "Vikram", "Neha",
    "Aditya", "Pooja", "Kiran", "Meera", "Sanjay",
]

LAST_NAMES = [
    "Sharma", "Reddy", "Kumar", "Patel", "Singh",
    "Verma", "Rao", "Gupta", "Nair", "Iyer",
]

DEPARTMENTS = ["Sales", "Operations", "Support", "Finance", "Marketing"]


def random_name():
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"


def random_date(start_date, end_date):
    days = (end_date - start_date).days
    return start_date + timedelta(days=random.randint(0, days))


def clear_sample_data(con):
    """Remove existing sample records before reseeding."""
    for table in ("order_items", "orders", "products", "employees", "customers"):
        con.execute(f"DELETE FROM {table}")

    print("Existing sample data cleared.")


def generate_customers(con):
    customers = []
    start_date = date(2022, 1, 1)
    end_date = date(2025, 12, 31)

    for customer_id in range(1, 1001):
        name = random_name()
        city = random.choice(CITIES)

        customers.append((
            customer_id,
            name,
            f"{name.lower().replace(' ', '.')}{customer_id}@example.com",
            city,
            STATES[city],
            "India",
            random_date(start_date, end_date),
            random.choice(["Standard", "Premium", "Enterprise"]),
        ))

    con.executemany(
        "INSERT INTO customers VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        customers,
    )
    print(f"Inserted {len(customers)} customers")


def generate_products(con):
    products = []
    product_id = 1

    for category, product_names in CATEGORIES.items():
        for product_name in product_names:
            for i in range(8):
                name = f"{product_name} {i + 1}"
                price = round(random.uniform(500, 100000), 2)
                cost = round(price * random.uniform(0.5, 0.85), 2)

                products.append((
                    product_id, name, category, product_name, price, cost
                ))
                product_id += 1

    con.executemany(
        "INSERT INTO products VALUES (?, ?, ?, ?, ?, ?)",
        products,
    )
    print(f"Inserted {len(products)} products")


def generate_employees(con):
    employees = []

    for employee_id in range(1, 51):
        employees.append((
            employee_id,
            random_name(),
            random.choice(DEPARTMENTS),
            random.choice(CITIES),
        ))

    con.executemany(
        "INSERT INTO employees VALUES (?, ?, ?, ?)",
        employees,
    )
    print(f"Inserted {len(employees)} employees")


def generate_orders(con):
    orders = []
    start_date = date(2023, 1, 1)
    end_date = date(2025, 12, 31)

    for order_id in range(1, 10001):
        sales_amount = round(random.uniform(500, 150000), 2)

        orders.append((
            order_id,
            random.randint(1, 1000),
            random.randint(1, 50),
            random_date(start_date, end_date),
            random.choices(
                ["Completed", "Pending", "Cancelled", "Returned"],
                weights=[75, 10, 8, 7],
            )[0],
            sales_amount,
            round(sales_amount * random.uniform(0, 0.20), 2),
            round(random.uniform(50, 1500), 2),
        ))

    con.executemany(
        "INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        orders,
    )
    print(f"Inserted {len(orders)} orders")


def generate_order_items(con):
    order_items = []
    order_item_id = 1

    for order_id in range(1, 10001):
        used_products = set()

        for _ in range(random.randint(1, 4)):
            product_id = random.randint(1, 200)

            while product_id in used_products:
                product_id = random.randint(1, 200)

            used_products.add(product_id)
            unit_price = round(random.uniform(500, 100000), 2)

            order_items.append((
                order_item_id,
                order_id,
                product_id,
                random.randint(1, 5),
                unit_price,
                round(unit_price * random.uniform(0, 0.15), 2),
            ))
            order_item_id += 1

    con.executemany(
        "INSERT INTO order_items VALUES (?, ?, ?, ?, ?, ?)",
        order_items,
    )
    print(f"Inserted {len(order_items)} order items")


def seed_database():
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DB_PATH}. Run create_database.py first."
        )

    con = duckdb.connect(str(DB_PATH))

    try:
        print("\nPreparing sample database...\n")
        clear_sample_data(con)
        generate_customers(con)
        generate_products(con)
        generate_employees(con)
        generate_orders(con)
        generate_order_items(con)
        print("\nDatabase seeding completed successfully!")
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


if __name__ == "__main__":
    seed_database()
