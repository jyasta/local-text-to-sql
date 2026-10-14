import duckdb
from pathlib import Path

DB_PATH = Path("data/database/analytics.duckdb")


def create_database():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect(str(DB_PATH))

    # -------------------------
    # Customers
    # -------------------------
    con.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            customer_id INTEGER PRIMARY KEY,
            customer_name VARCHAR,
            email VARCHAR,
            city VARCHAR,
            state VARCHAR,
            country VARCHAR,
            signup_date DATE,
            customer_segment VARCHAR
        )
    """)

    # -------------------------
    # Products
    # -------------------------
    con.execute("""
        CREATE TABLE IF NOT EXISTS products (
            product_id INTEGER PRIMARY KEY,
            product_name VARCHAR,
            category VARCHAR,
            subcategory VARCHAR,
            price DECIMAL(10,2),
            cost DECIMAL(10,2)
        )
    """)

    # -------------------------
    # Employees
    # -------------------------
    con.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            employee_id INTEGER PRIMARY KEY,
            employee_name VARCHAR,
            department VARCHAR,
            city VARCHAR
        )
    """)

    # -------------------------
    # Orders
    # -------------------------
    con.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY,
            customer_id INTEGER,
            employee_id INTEGER,
            order_date DATE,
            status VARCHAR,
            sales_amount DECIMAL(10,2),
            discount DECIMAL(10,2),
            shipping_cost DECIMAL(10,2)
        )
    """)

    # -------------------------
    # Order Items
    # -------------------------
    con.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            order_item_id INTEGER PRIMARY KEY,
            order_id INTEGER,
            product_id INTEGER,
            quantity INTEGER,
            unit_price DECIMAL(10,2),
            discount DECIMAL(10,2)
        )
    """)

    con.close()

    print("Database created successfully!")
    print(f"Location: {DB_PATH}")


if __name__ == "__main__":
    create_database()