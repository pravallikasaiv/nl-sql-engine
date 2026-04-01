import sqlite3
import os

DB_PATH = "sales.db"

def create_and_seed_database():
    """Creates the database and inserts sample data if it doesn't exist"""
    if os.path.exists(DB_PATH):
        return  # Already exists, skip

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            customer_id   INTEGER PRIMARY KEY,
            name          TEXT NOT NULL,
            email         TEXT,
            city          TEXT,
            country       TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            product_id    INTEGER PRIMARY KEY,
            product_name  TEXT NOT NULL,
            category      TEXT,
            price         REAL
        )
    """)

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

    customers = [
        (1, "Alice Johnson",  "alice@email.com",   "New York",      "USA"),
        (2, "Bob Smith",      "bob@email.com",      "London",        "UK"),
        (3, "Carol White",    "carol@email.com",    "Toronto",       "Canada"),
        (4, "David Lee",      "david@email.com",    "Sydney",        "Australia"),
        (5, "Eva Martinez",   "eva@email.com",      "New York",      "USA"),
        (6, "Frank Chen",     "frank@email.com",    "San Francisco", "USA"),
        (7, "Grace Kim",      "grace@email.com",    "London",        "UK"),
        (8, "Henry Brown",    "henry@email.com",    "Toronto",       "Canada"),
    ]

    products = [
        (1, "Laptop Pro",     "Electronics", 1200.00),
        (2, "Wireless Mouse", "Electronics",   45.00),
        (3, "Standing Desk",  "Furniture",    650.00),
        (4, "Monitor 4K",     "Electronics",  380.00),
        (5, "Office Chair",   "Furniture",    420.00),
        (6, "USB-C Hub",      "Electronics",   55.00),
        (7, "Notebook Set",   "Stationery",    18.00),
        (8, "Webcam HD",      "Electronics",   95.00),
    ]

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
    conn.close()
    print("✅ Database created and seeded")


if __name__ == "__main__":
    create_and_seed_database()