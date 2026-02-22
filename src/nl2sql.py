"""
Natural Language to SQL (NL2SQL) for the Supply Chain RAG project.

This module implements the NL2SQL pipeline:
- Load database schema and pass it to the LLM
- Convert natural language questions into SQL SELECT queries
- Execute the SQL against the database
- Return or format the results as the answer

This addresses the requirement that the model must understand the database
schema and generate queries based on that understanding.
"""

from __future__ import annotations

import re
from typing import List, Optional

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

from .db import get_schema_description, initialize_database, run_query


def _extract_sql_from_response(text: str) -> Optional[str]:
    """
    Try to extract a SQL query from the LLM's response.
    The model might wrap the query in markdown code blocks or return it inline.
    """
    # Look for ```sql ... ``` or ``` ... ```
    block_match = re.search(r"```(?:sql)?\s*([\s\S]*?)```", text, re.IGNORECASE)
    if block_match:
        return block_match.group(1).strip()
    # Fallback: look for SELECT ... (up to semicolon or end)
    select_match = re.search(r"(SELECT\s[\s\S]*?)(?:;|\n\n|$)", text, re.IGNORECASE | re.DOTALL)
    if select_match:
        return select_match.group(1).strip()
    return None


def _validate_select_only(sql: str) -> bool:
    """
    Ensure the generated SQL is a SELECT query only (no modifications).
    """
    stripped = sql.strip().upper()
    # Must start with SELECT
    if not stripped.startswith("SELECT"):
        return False
    # Block dangerous keywords
    dangerous = ["DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "CREATE", "TRUNCATE"]
    for kw in dangerous:
        if re.search(rf"\b{kw}\b", stripped):
            return False
    return True


def generate_sql(question: str, schema: str, model: str = "mistral") -> Optional[str]:
    """
    Use the LLM to generate a SQL query from a natural language question.

    Args:
        question: The user's natural language question.
        schema: The database schema description (from get_schema_description).
        model: Ollama model name (default: mistral).

    Returns:
        The generated SQL string, or None if generation failed.
    """
    system = SystemMessage(
        content=(
            "You are a SQL expert for a SQLite supply chain database. "
            "Given a natural language question and the database schema, "
            "generate a single SQLite-compatible SELECT query that answers the question. "
            "Use only the tables and columns described in the schema. "
            "Return ONLY the SQL query, no explanation. Use SQLite syntax "
            "(e.g., use || for string concatenation, no LIMIT 0, 5)."
        )
    )
    human = HumanMessage(
        content=f"{schema}\n\nQuestion: {question}\n\nSQL query:"
    )

    llm = ChatOllama(model=model)
    response = llm.invoke([system, human])
    raw = response.content or ""

    sql = _extract_sql_from_response(raw)
    if sql and _validate_select_only(sql):
        return sql
    return None


def format_results_as_text(rows: List[dict], max_rows: int = 20) -> str:
    """
    Convert query results into readable text for the user or for a follow-up LLM.
    """
    if not rows:
        return "No rows returned."
    if len(rows) > max_rows:
        truncated = rows[:max_rows]
        suffix = f"\n... and {len(rows) - max_rows} more rows."
    else:
        truncated = rows
        suffix = ""

    lines = []
    for i, row in enumerate(truncated, start=1):
        parts = [f"{k}={v}" for k, v in row.items()]
        lines.append(f"  {i}. " + ", ".join(parts))
    return "\n".join(lines) + suffix


def answer_question_nl2sql(
    question: str,
    model: str = "mistral",
    max_results: int = 20,
) -> str:
    """
    End-to-end NL2SQL: natural language question → SQL → execute → formatted answer.

    Args:
        question: The user's question about the supply chain data.
        model: Ollama model name.
        max_results: Max rows to include in the formatted output.

    Returns:
        A human-readable answer based on the query results, or an error message.
    """
    initialize_database(force_recreate=False)
    schema = get_schema_description()

    sql = generate_sql(question, schema, model=model)
    if not sql:
        return (
            "I couldn't generate a valid SQL query for that question. "
            "Try asking about data in the supply chain (e.g., products, orders, "
            "suppliers, inventory, prices, quantities)."
        )

    try:
        rows = run_query(sql)
        result_text = format_results_as_text(rows, max_rows=max_results)
        if not rows:
            return f"No matching data found for: \"{question}\""
        return f"Query results:\n{result_text}"
    except Exception as e:
        return (
            f"The generated query failed: {e}\n\n"
            f"Generated SQL: {sql}\n\n"
            "Please try rephrasing your question."
        )
