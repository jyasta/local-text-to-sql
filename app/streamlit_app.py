
import sys
from pathlib import Path
from decimal import Decimal
import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline import TextToSQLPipeline


st.set_page_config(
    page_title="Local Text-to-SQL",
    page_icon="🧠",
    layout="wide",
)

st.title("🧠 Local Text-to-SQL")
st.caption("Ask questions about your data using a local AI pipeline.")

st.success("🔒 Local AI  •  Local Database  •  No Cloud LLM API")

@st.cache_resource
def load_pipeline():
    return TextToSQLPipeline(max_attempts=3)

with st.spinner("Loading the local Text-to-SQL pipeline..."):
    pipeline = load_pipeline()

st.divider()

st.subheader("Ask your database")

examples = [
    "Show the top 5 customers by revenue.",
    "What is the average order value?",
    "Show total sales by department.",
    "Show revenue for orders placed in 2025.",
    "Show the top 5 product categories by sales.",
]

selected_example = st.selectbox(
    "Choose an example question",
    ["Custom question"] + examples,
)

default_question = (
    "" if selected_example == "Custom question"
    else selected_example
)

question = st.text_area(
    "Your question",
    value=default_question,
    placeholder="Example: Show the top 10 customers by revenue.",
    height=100,
)

run_query = st.button(
    "Generate SQL and Run",
    type="primary",
    use_container_width=True,
)

if run_query:
    if not question.strip():
        st.warning("Please enter a question.")
    else:
        try:
            with st.spinner("Analyzing your question and running SQL..."):
                result = pipeline.process(question.strip())

            st.session_state["last_result"] = result
            st.session_state["last_question"] = question.strip()

        except Exception as error:
            st.error(f"Something went wrong: {error}")

result = st.session_state.get("last_result")

if result:
    st.divider()
    st.subheader("Query overview")

    col1, col2 = st.columns(2)

    with col1:
        if result.get("success"):
            st.success("Query executed successfully")
        else:
            st.error("Query execution failed")

    with col2:
        st.info("Database: DuckDB • Read-only connection")

    st.subheader("Generated SQL")

    sql = result.get("sql") or "-- No SQL generated"

    st.code(sql, language="sql")

    st.download_button(
        "Download SQL",
        data=sql,
        file_name="generated_query.sql",
        mime="text/sql",
    )

    if result.get("error"):
        st.error(result["error"])

    if result.get("success"):
        st.subheader("Query results")

        columns = result.get("columns", [])
        rows = result.get("rows", [])

        if rows:
            dataframe = pd.DataFrame(rows, columns=columns)

            # Convert Decimal values to floats for display and CSV export.
            for column in dataframe.columns:
                dataframe[column] = dataframe[column].map(
                    lambda value: (
                        float(value)
                        if isinstance(value, Decimal)
                        else value
                    )
                )

            st.caption(f"{len(dataframe):,} row(s) returned")

            st.dataframe(
                dataframe,
                use_container_width=True,
                hide_index=True,
            )

            csv_data = dataframe.to_csv(index=False).encode("utf-8")

            st.download_button(
                "Download results as CSV",
                data=csv_data,
                file_name="query_results.csv",
                mime="text/csv",
            )
        else:
            st.info("The query ran successfully but returned no rows.")

st.divider()

with st.expander("About this application"):
    st.write(
        "This project converts natural-language questions into SQL, "
        "retrieves relevant schema information, validates SQL, and "
        "executes permitted queries against a local DuckDB database."
    )
    st.caption(
        "Note: Qwen currently returns empty output in this environment, "
        "so the deterministic fallback generates SQL for supported intents."
    )
