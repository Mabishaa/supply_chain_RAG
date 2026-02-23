"""
Streamlit UI for the Supply Chain NL2SQL QA system.

This is a thin UI layer on top of the existing `simple_qa.answer_question`
function. It does NOT change the core logic of the project.
"""

from __future__ import annotations

import textwrap

import streamlit as st

from simple_qa import answer_question


def main() -> None:
    st.set_page_config(
        page_title="Supply Chain NL2SQL QA",
        page_icon="📦",
        layout="centered",
    )

    st.title("Supply Chain NL2SQL QA")
    st.caption(
        "Ask questions in natural language. The system converts them to SQL "
        "using the database schema and runs them against your supply chain data."
    )

    with st.expander("ℹ️ How this works", expanded=False):
        st.write(
            textwrap.dedent(
                """
                - Your question is sent to an LLM together with the database schema
                - The model generates a **SQLite SELECT query**
                - The query is executed on the local SQLite database
                - The results are shown below

                Make sure:
                - The SQLite DB is initialized (the code does this automatically)
                - Ollama is running and the `mistral` model is available
                """
            )
        )

    st.markdown("### Ask a question")
    default_example = (
        "Examples:\n"
        "- How many products are there?\n"
        "- List the top 5 products by selling price.\n"
        "- Which suppliers provide products to inventory 1?\n"
        "- Show total sale_amount per product."
    )
    question = st.text_area(
        "Your question about the supply chain data:",
        height=120,
        placeholder=default_example,
    )

    col1, col2 = st.columns([1, 3])
    with col1:
        run_clicked = st.button("Ask", type="primary")
    with col2:
        clear_clicked = st.button("Clear")

    if clear_clicked:
        st.experimental_rerun()

    if run_clicked and question.strip():
        with st.spinner("Thinking (converting to SQL and querying the DB)..."):
            try:
                answer = answer_question(question.strip())
            except Exception as e:  # pragma: no cover - UI-only error path
                st.error(f"Something went wrong: {e}")
                return

        st.markdown("### Answer")
        st.write(answer)


if __name__ == "__main__":
    main()

