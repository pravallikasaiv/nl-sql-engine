import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import datetime
from engine import NLSQLEngine



st.set_page_config(
    page_title="NL → SQL Engine",
    page_icon="🔍",
    layout="wide"
)

def load_csv_into_db(uploaded_file):
    df = pd.read_csv(uploaded_file)
    cleaned = []
    for col in df.columns:
        col = col.strip().lower()
        col = col.replace(" ", "_")
        col = "".join(c for c in col if c.isalnum() or c == "_")
        cleaned.append(col)
    df.columns = cleaned
    table_name = uploaded_file.name.replace(".csv", "").lower().replace(" ", "_")
    conn = sqlite3.connect("sales.db")
    df.to_sql(table_name, conn, if_exists="replace", index=False)
    conn.close()
    return table_name, df


def load_default_engine():
    return NLSQLEngine()


def display_result(res):
    st.divider()
    if res["success"]:
        st.markdown("### Answer")
        st.success(res["answer"])
        if res["rows"]:
            st.markdown("### Results")
            df = pd.DataFrame(res["rows"], columns=res["columns"])
            st.dataframe(df, use_container_width=True, hide_index=True)
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download results as CSV",
                data=csv,
                file_name="query_results.csv",
                mime="text/csv"
            )
        else:
            st.info("Query ran successfully but returned no rows.")
        st.markdown("### Generated SQL")
        st.code(res["sql"], language="sql")
    else:
        st.error(res["error"])


def add_to_history(question: str, success: bool):
    if "history" not in st.session_state:
        st.session_state["history"] = []
    st.session_state["history"].insert(0, {
        "question": question,
        "time": datetime.now().strftime("%I:%M %p"),
        "success": success
    })
    st.session_state["history"] = st.session_state["history"][:10]


# -----------------------------------------------------------
# Initialize session state
# -----------------------------------------------------------
if "last_result" not in st.session_state:
    st.session_state["last_result"] = None
if "last_question" not in st.session_state:
    st.session_state["last_question"] = None
if "history" not in st.session_state:
    st.session_state["history"] = []

# -----------------------------------------------------------
# Load engine
# -----------------------------------------------------------
engine = load_default_engine()

# -----------------------------------------------------------
# Sidebar
# -----------------------------------------------------------
with st.sidebar:
    st.markdown("### Data source")
    data_source = st.radio(
        "Choose your data:",
        ["Use sample sales data", "Upload my own CSV"]
    )

    if data_source == "Upload my own CSV":
        uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])
        if uploaded_file:
            table_name, df = load_csv_into_db(uploaded_file)
            st.success(f"Loaded: {uploaded_file.name}")
            st.markdown("**Preview (first 5 rows):**")
            st.dataframe(df.head(), use_container_width=True)
            st.markdown("**Columns detected:**")
            for col, dtype in df.dtypes.items():
                st.markdown(f"- `{col}` ({dtype})")
            engine.schema = engine._get_schema()
        else:
            st.info("Please upload a CSV file.")
    else:
        st.markdown("### Database schema")
        st.code(engine.schema, language="text")

    st.divider()

    st.markdown("### Query history")
    if not st.session_state["history"]:
        st.caption("No queries yet — ask a question to get started.")
    else:
        if st.button("Clear history", use_container_width=True):
            st.session_state["history"] = []
            st.session_state["last_result"] = None
            st.session_state["last_question"] = None
            st.rerun()

        for item in st.session_state["history"]:
            icon = "✅" if item["success"] else "❌"
            label = item["question"]
            if len(label) > 40:
                label = label[:40] + "..."
            st.markdown(f"{icon} `{item['time']}` — {label}")

    st.divider()
    st.markdown("Built with Claude API + Streamlit")

# -----------------------------------------------------------
# Main
# -----------------------------------------------------------
st.title("🔍 NL → SQL Query Engine")
st.markdown("Ask questions about your data in plain English. Powered by Claude AI.")
st.divider()

# -----------------------------------------------------------
# Example buttons
# -----------------------------------------------------------
st.markdown("**Try an example:**")
col1, col2, col3 = st.columns(3)

clicked_question = None

with col1:
    if st.button("Top 3 customers", use_container_width=True):
        clicked_question = "Who are the top 3 customers by total spending?"
with col2:
    if st.button("Best product category", use_container_width=True):
        clicked_question = "What is the best selling product category?"
with col3:
    if st.button("Orders from USA", use_container_width=True):
        clicked_question = "How many orders came from the USA?"

st.divider()

# -----------------------------------------------------------
# Manual question input
# -----------------------------------------------------------
st.markdown("**Or type your own question:**")
question = st.text_input(
    label="Your question:",
    placeholder="e.g. What is the total revenue by country?",
)

if st.button("Ask", type="primary", use_container_width=True):
    if question.strip():
        clicked_question = question
    else:
        st.warning("Please enter a question first.")

# -----------------------------------------------------------
# Run query — store result in session state then rerun
# -----------------------------------------------------------
if clicked_question:
    with st.spinner("Thinking..."):
        query_result = engine.ask(clicked_question)
    add_to_history(clicked_question, query_result["success"])
    st.session_state["last_result"] = query_result
    st.session_state["last_question"] = clicked_question
    st.rerun()

# -----------------------------------------------------------
# Display last result
# -----------------------------------------------------------
if st.session_state["last_result"] is not None:
    st.markdown(f"**Question:** {st.session_state['last_question']}")
    display_result(st.session_state["last_result"])