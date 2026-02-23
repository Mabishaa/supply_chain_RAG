"""
Phase 1 demo script:

- Initialize the SQLite database from the SQL scripts (if not already done)
- Run a simple SELECT query to fetch sample product rows
- Convert those rows into clean text documents, ready for embedding later

This gives you an end-to-end path from:
  SQL files -> SQLite DB -> Python rows -> natural language text
"""

from __future__ import annotations

from typing import List

from .db import get_sample_rows, initialize_database
from .text_utils import product_row_to_text


def build_product_text_corpus(limit: int = 20) -> List[str]:
    """
    Fetch a number of product rows and convert them into text snippets.

    WHY: Phase 1 of the RAG pipeline is about proving we can reliably
    extract structured data and turn it into textual "documents".
    """
    rows = get_sample_rows(limit=limit)
    docs = [product_row_to_text(row) for row in rows]
    return docs


def main() -> None:
    # 1. Ensure the SQLite DB exists and is populated.
    initialize_database(force_recreate=False)

    # 2. Build a small text corpus from product data.
    docs = build_product_text_corpus(limit=10)

    # 3. Print the documents so you can visually inspect them.
    print("Product text documents (ready for embedding):\n")
    for i, doc in enumerate(docs, start=1):
        print(f"[DOC {i}] {doc}")


if __name__ == "__main__":
    main()

