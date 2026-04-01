import sqlite3
import re
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

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


class NLSQLEngine:

    def __init__(self):
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
        """
        Remove markdown formatting Claude sometimes adds
        even when told not to. Handles cases like:
```sql
        SELECT ...
```
        """
        # Strip markdown code blocks if present
        raw = re.sub(r"```(?:sql)?", "", raw, flags=re.IGNORECASE)
        raw = raw.replace("`", "").strip()
        return raw

    def _is_safe_sql(self, sql: str) -> bool:
        """
        Only allow SELECT statements.
        Blocks DROP, DELETE, INSERT, UPDATE — protects your database.
        """
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
            # Step 1 — generate SQL
            sql = self.generate_sql(question)

            # Step 2 — check if Claude couldn't answer
            if "CANNOT_ANSWER" in sql.upper():
                return {
                    "success": False,
                    "question": question,
                    "error": "I can only answer questions about "
                             "customers, products, and orders."
                }

            # Step 3 — safety check (SELECT only)
            if not self._is_safe_sql(sql):
                return {
                    "success": False,
                    "question": question,
                    "error": "Only SELECT queries are allowed."
                }

            # Step 4 — run SQL
            columns, rows = self.run_sql(sql)

            # Step 5 — explain results
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


if __name__ == "__main__":
    engine = NLSQLEngine()

    # Normal questions
    questions = [
        "Who are the top 3 customers by total spending?",
        "What is the average order value?",
    ]

    # Edge cases — these should fail gracefully
    edge_cases = [
        "What is the weather in New York?",   # unrelated question
        "Delete all customers",               # dangerous SQL
        "asdfjkl",                            # gibberish
    ]

    print("=== Normal questions ===")
    for q in questions:
        result = engine.ask(q)
        print(f"\nQ: {q}")
        if result["success"]:
            print(f"SQL: {result['sql']}")
            print(f"Answer: {result['answer']}")
        else:
            print(f"Handled gracefully: {result['error']}")

    print("\n=== Edge cases ===")
    for q in edge_cases:
        result = engine.ask(q)
        print(f"\nQ: {q}")
        if result["success"]:
            print(f"Answer: {result['answer']}")
        else:
            print(f"Handled gracefully: {result['error']}")