"""
Simple QA over the Supply Chain database using NL2SQL.

Pipeline:
- Load the SQLite DB (created from your SQL scripts)
- Let the user type a natural-language question
- Use NL2SQL: pass the database schema to the LLM, which generates a SQL query
- Execute the query against the database
- Return the results

The model answers based on its understanding of the database schema
(converting natural language to SQL), not from a static text corpus.
"""

from __future__ import annotations

from .nl2sql import answer_question_nl2sql


def answer_question(question: str) -> str:
    """
    Answer a natural language question by converting it to SQL and executing
    against the supply chain database (NL2SQL).
    """
    return answer_question_nl2sql(question)


def main() -> None:
    print("Supply Chain QA (NL2SQL via mistral/Ollama).")
    print("Questions are converted to SQL using the database schema.")
    print("Make sure Ollama is running and the 'mistral' model is pulled.")
    print("Type 'exit' or press Ctrl+C to quit.\n")

    while True:
        try:
            question = input("Your question about the supply chain> ").strip()
            if not question or question.lower() in {"exit", "quit"}:
                break

            answer = answer_question(question)
            print("\n--- Answer ---")
            print(answer)
            print("--------------\n")
        except KeyboardInterrupt:
            print("\nExiting.")
            break


if __name__ == "__main__":
    main()

