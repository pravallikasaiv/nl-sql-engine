import os
import sqlite3
import re
import streamlit as st
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

# Works both locally (.env) and on Streamlit Cloud (st.secrets)
if "ANTHROPIC_API_KEY" in st.secrets:
    os.environ["ANTHROPIC_API_KEY"] = st.secrets["ANTHROPIC_API_KEY"]

DB_PATH = "sales.db"

SQL_PROMPT = """
You are a SQL expert working with a SQLite database.

DATABASE SCHEMA:
{schema}

RULES:
1. Return ONLY the raw SQL query — no explanation, no markdown, no backticks
2. Use exact table and column names from the schema above
3. Always use proper JOINs when data spans multiple tables
4. For "top N" questions always use ORDER BY + LIMIT
5. For revenue/totals always use SUM()
6. If the question cannot be answered from the schema, return exactly: CANNOT_ANSWER

EXAMPLE:
Question: How many customers are from USA?
SQL: SELECT COUNT(*) FROM customers WHERE country = 'USA'

Now convert this question to SQL:
{question}
"""

EXPLAIN_PROMPT = """
A user asked: "{question}"

The SQL query returned these results:
Columns: {columns}
Rows: {rows}

Give a clear, friendly 1-2 sentence summary of what the results mean.
Do not mention SQL. Speak directly to the user as if explaining the answer.
If the results are empty, say no data was found for that question.
"""


def create_and_seed_database():
    """Creates and seeds the database — runs on every startup"""
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


class NLSQLEngine:

    def __init__(self):
        create_and_seed_database()
        self.client = Anthropic()
        self.schema = self._get_schema()

    def _get_schema(self) -> str:
        conn = sqlite3.connect(DB_PATH)
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

        conn.close()
        return schema

    def _clean_sql(self, raw: str) -> str:
        raw = re.sub(r"```(?:sql)?", "", raw, flags=re.IGNORECASE)
        raw = raw.replace("`", "").strip()
        return raw

    def _is_safe_sql(self, sql: str) -> bool:
        first_word = sql.strip().split()[0].upper()
        return first_word == "SELECT"

    def generate_sql(self, question: str) -> str:
        prompt = SQL_PROMPT.format(
            schema=self.schema,
            question=question
        )
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}]
        )
        return self._clean_sql(response.content[0].text)

    def run_sql(self, sql: str):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(sql)
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        conn.close()
        return columns, rows

    def explain_results(self, question: str,
                        columns: list, rows: list) -> str:
        prompt = EXPLAIN_PROMPT.format(
            question=question,
            columns=columns,
            rows=rows
        )
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text.strip()

    def ask(self, question: str) -> dict:
        try:
            sql = self.generate_sql(question)

            if "CANNOT_ANSWER" in sql.upper():
                return {
                    "success": False,
                    "question": question,
                    "error": "I can only answer questions about "
                             "customers, products, and orders."
                }

            if not self._is_safe_sql(sql):
                return {
                    "success": False,
                    "question": question,
                    "error": "Only SELECT queries are allowed."
                }

            columns, rows = self.run_sql(sql)
            answer = self.explain_results(question, columns, rows)

            return {
                "success":  True,
                "question": question,
                "sql":      sql,
                "columns":  columns,
                "rows":     rows,
                "answer":   answer
            }

        except sqlite3.OperationalError as e:
            return {
                "success": False,
                "question": question,
                "error": f"Database error: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "question": question,
                "error": f"Something went wrong: {str(e)}"
            }