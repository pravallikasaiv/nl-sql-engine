import sqlite3
import csv
import os

DB_PATH = "sales.db"

def create_database():
    """
    Creates a SQLite database with 3 tables:
    - customers
    - products  
    - orders
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create customers table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            customer_id   INTEGER PRIMARY KEY,
            name          TEXT NOT NULL,
            email         TEXT,
            city          TEXT,
            country       TEXT
        )
    """)

    # Create products table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            product_id    INTEGER PRIMARY KEY,
            product_name  TEXT NOT NULL,
            category      TEXT,
            price         REAL
        )
    """)

    # Create orders table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id      INTEGER PRIMARY KEY,
            customer_id   INTEGER,
            product_id    INTEGER,
            quantity      INTEGER,
            order_date    TEXT,
            total_amount  REAL,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
            FOREIGN KEY (product_id)  REFERENCES products(product_id)
        )
    """)

    conn.commit()
    print("✅ Tables created")
    return conn


def insert_sample_data(conn):
    """Insert realistic sample data"""
    cursor = conn.cursor()

    # Sample customers
    customers = [
        (1, "Alice Johnson",  "alice@email.com",  "New York",    "USA"),
        (2, "Bob Smith",      "bob@email.com",     "London",      "UK"),
        (3, "Carol White",    "carol@email.com",   "Toronto",     "Canada"),
        (4, "David Lee",      "david@email.com",   "Sydney",      "Australia"),
        (5, "Eva Martinez",   "eva@email.com",     "New York",    "USA"),
        (6, "Frank Chen",     "frank@email.com",   "San Francisco","USA"),
        (7, "Grace Kim",      "grace@email.com",   "London",      "UK"),
        (8, "Henry Brown",    "henry@email.com",   "Toronto",     "Canada"),
    ]

    # Sample products
    products = [
        (1, "Laptop Pro",      "Electronics",  1200.00),
        (2, "Wireless Mouse",  "Electronics",    45.00),
        (3, "Standing Desk",   "Furniture",     650.00),
        (4, "Monitor 4K",      "Electronics",   380.00),
        (5, "Office Chair",    "Furniture",     420.00),
        (6, "USB-C Hub",       "Electronics",    55.00),
        (7, "Notebook Set",    "Stationery",     18.00),
        (8, "Webcam HD",       "Electronics",    95.00),
    ]

    # Sample orders
    orders = [
        (1,  1, 1, 1, "2024-01-15", 1200.00),
        (2,  2, 2, 3, "2024-01-18",  135.00),
        (3,  3, 3, 1, "2024-01-20",  650.00),
        (4,  1, 4, 2, "2024-02-01",  760.00),
        (5,  4, 5, 1, "2024-02-05",  420.00),
        (6,  5, 1, 1, "2024-02-10", 1200.00),
        (7,  2, 6, 4, "2024-02-14",  220.00),
        (8,  6, 2, 2, "2024-02-20",   90.00),
        (9,  7, 8, 1, "2024-03-01",   95.00),
        (10, 3, 4, 1, "2024-03-05",  380.00),
        (11, 1, 6, 2, "2024-03-10",  110.00),
        (12, 8, 1, 1, "2024-03-12", 1200.00),
        (13, 5, 3, 1, "2024-03-18",  650.00),
        (14, 4, 7, 5, "2024-03-22",   90.00),
        (15, 6, 5, 1, "2024-04-01",  420.00),
    ]

    cursor.executemany(
        "INSERT OR IGNORE INTO customers VALUES (?,?,?,?,?)", customers)
    cursor.executemany(
        "INSERT OR IGNORE INTO products VALUES (?,?,?,?)", products)
    cursor.executemany(
        "INSERT OR IGNORE INTO orders VALUES (?,?,?,?,?,?)", orders)

    conn.commit()
    print("✅ Sample data inserted")


def get_schema(conn):
    """
    CONCEPT: This is your RAG context.
    You'll inject this into every Claude prompt on Day 5
    so Claude knows your exact table and column names.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()

    schema = ""
    for (table_name,) in tables:
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        col_defs = ", ".join(
            f"{col[1]} ({col[2]})" for col in columns
        )
        schema += f"Table: {table_name} — Columns: {col_defs}\n"

    return schema


def test_queries(conn):
    """Run a few raw SQL queries to verify data is correct"""
    cursor = conn.cursor()

    print("\n--- Top 3 customers by total spend ---")
    cursor.execute("""
        SELECT c.name, SUM(o.total_amount) as total
        FROM customers c
        JOIN orders o ON c.customer_id = o.customer_id
        GROUP BY c.name
        ORDER BY total DESC
        LIMIT 3
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]}: ${row[1]:.2f}")

    print("\n--- Orders per product category ---")
    cursor.execute("""
        SELECT p.category, COUNT(*) as order_count, SUM(o.total_amount) as revenue
        FROM products p
        JOIN orders o ON p.product_id = o.product_id
        GROUP BY p.category
        ORDER BY revenue DESC
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]} orders, ${row[2]:.2f} revenue")


if __name__ == "__main__":
    print("Building sales database...\n")
    conn = create_database()
    insert_sample_data(conn)

    print("\n--- Your database schema (this becomes your RAG context) ---")
    print(get_schema(conn))

    test_queries(conn)

    conn.close()
    print("\n✅ Day 2 complete! sales.db is ready.")