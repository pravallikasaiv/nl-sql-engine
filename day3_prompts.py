import sqlite3
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic()
DB_PATH = "sales.db"


def get_schema():
    """Fetch real schema from your database — this is your RAG context"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()

    schema = ""
    for (table_name,) in tables:
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        col_defs = ", ".join(f"{col[1]} ({col[2]})" for col in columns)
        schema += f"Table: {table_name} — Columns: {col_defs}\n"

    conn.close()
    return schema


# -------------------------------------------------------
# CONCEPT: Prompt Engineering
# The better your prompt, the better Claude's SQL.
# We try 3 versions below — watch how the output improves.
# -------------------------------------------------------

# VERSION 1 — Bad prompt (no schema, no instructions)
BAD_PROMPT = """
Convert this question to SQL: {question}
"""

# VERSION 2 — Better prompt (has schema, basic instructions)
BETTER_PROMPT = """
You are a SQL expert. Given this database schema:
{schema}

Convert this question to SQL:
{question}
"""

# VERSION 3 — Best prompt (schema + strict rules + example)
BEST_PROMPT = """
You are a SQL expert working with a SQLite database.

DATABASE SCHEMA:
{schema}

RULES:
1. Return ONLY the raw SQL query — no explanation, no markdown, no backticks
2. Use exact table and column names from the schema above
3. Always use proper JOINs when data spans multiple tables
4. For "top N" questions always use ORDER BY + LIMIT
5. For revenue/totals always use SUM()

EXAMPLE:
Question: How many customers are from USA?
SQL: SELECT COUNT(*) FROM customers WHERE country = 'USA'

Now convert this question to SQL:
{question}
"""


def ask_claude_sql(prompt_template: str, question: str) -> str:
    schema = get_schema()
    prompt = prompt_template.format(schema=schema, question=question)

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text.strip()


def run_sql(sql: str) -> list:
    """Execute the generated SQL and return results"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(sql)
        results = cursor.fetchall()
        conn.close()
        return results
    except Exception as e:
        return [f"SQL Error: {e}"]


def compare_prompts():
    question = "Who are the top 3 customers by total amount spent?"

    print("=" * 60)
    print(f"Question: {question}")
    print("=" * 60)

    for label, template in [
        ("BAD PROMPT",    BAD_PROMPT),
        ("BETTER PROMPT", BETTER_PROMPT),
        ("BEST PROMPT",   BEST_PROMPT),
    ]:
        print(f"\n--- {label} ---")
        sql = ask_claude_sql(template, question)
        print(f"SQL generated:\n{sql}")

        results = run_sql(sql)
        print(f"Results: {results}")


def interactive_mode():
    """Ask questions using the best prompt and see real results"""
    schema = get_schema()
    print("\n" + "=" * 60)
    print("  NL → SQL Engine  |  Day 3: Best Prompt + Live Results")
    print("=" * 60)
    print("Type a question. Type 'quit' to exit.\n")

    while True:
        question = input("You: ").strip()
        if question.lower() in ("quit", "exit", "q"):
            break
        if not question:
            continue

        # Generate SQL
        sql = ask_claude_sql(BEST_PROMPT, question)
        print(f"\nSQL: {sql}")

        # Run it against your real database
        results = run_sql(sql)
        print(f"Results: {results}\n")


if __name__ == "__main__":
    # First show how prompt quality affects output
    compare_prompts()

    # Then go interactive
    interactive_mode()