# NL → SQL Query Engine

Ask questions about your data in plain English. 
Powered by Claude AI and Streamlit.

🔗 **Live Demo:** [your-streamlit-url-here]

---

## What it does

This app lets you query a database using plain English instead of SQL.
Type a question like *"Who are the top 3 customers by revenue?"* and the app:

1. Sends your question + database schema to Claude AI
2. Claude generates the correct SQL query
3. The query runs against a real SQLite database
4. Claude explains the results in plain English
5. Results are displayed as an interactive table

---

## Features

- Natural language to SQL conversion using Claude API
- RAG architecture — database schema injected into every prompt
- Error handling for unsafe queries and unrelated questions
- CSV upload — query any dataset, not just the sample data
- Query history tracked in the sidebar
- Download results as CSV
- Deployed live on Streamlit Cloud

---

## Tech stack

| Layer | Tool |
|---|---|
| Language | Python 3.9 |
| LLM | Claude API (Anthropic) |
| Database | SQLite |
| Data processing | Pandas |
| UI | Streamlit |
| Deployment | Streamlit Cloud |
| Version control | GitHub |

---

## How it works
```
User question
     ↓
Schema fetched from SQLite (RAG context)
     ↓
Claude generates SQL using schema + question
     ↓
SQL executed against database
     ↓
Claude explains results in plain English
     ↓
Results displayed as interactive table
```

---

## Run locally

**1. Clone the repo**
```bash
git clone https://github.com/pravallikasaiv/nl-sql-engine.git
cd nl-sql-engine
```

**2. Create virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**3. Add your API key**
```bash
echo "ANTHROPIC_API_KEY=your_key_here" > .env
```

**4. Run the app**
```bash
streamlit run app.py
```

---

## Sample questions to try

- Who are the top 3 customers by total spending?
- What is the best selling product category?
- How many orders came from the USA?
- What is the average order value?
- Which month had the most orders?

---

## Project structure
```
nl-sql-engine/
├── app.py          # Streamlit UI
├── engine.py       # NLSQLEngine class — Claude API + SQL logic
├── requirements.txt
└── README.md
```

---

Built by Pravallika Dasari
