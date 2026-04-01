import os
from anthropic import Anthropic
from dotenv import load_dotenv

# Loads your API key from .env file
load_dotenv()

# Creates your connection to Claude
client = Anthropic()

# Sets Claude's behavior for every message
SYSTEM_PROMPT = """
You are a helpful data assistant. Answer questions clearly and concisely.
When asked about data, always suggest what SQL query might answer the question.
"""

def ask_claude(question: str) -> str:
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": question}
        ]
    )
    print(f"\n--- RAW RESPONSE ---")
    print(response)
    print(f"--- END ---\n")
    return response.content[0].text


def main():
    print("=" * 50)
    print("  NL → SQL Engine  |  Day 1: Hello Claude!")
    print("=" * 50)
    print("Type your question. Type 'quit' to exit.\n")

    while True:
        question = input("You: ").strip()

        if question.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break

        if not question:
            continue

        print("\nClaude:", ask_claude(question))
        print()

if __name__ == "__main__":
    main()