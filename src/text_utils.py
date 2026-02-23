"""
Utilities to convert database rows into natural-language text documents.

In a RAG pipeline, we need textual "documents" that:
- capture the important information from each row (or group of rows)
- are readable by an LLM
- are consistent in structure so retrieval remains interpretable

This module will later be used by the embedding + vector-store steps.
"""

from __future__ import annotations

from typing import Dict, List


def customer_row_to_text(row: Dict) -> str:
    """
    Convert a single customer row into a short natural language description.

    WHY: This is where we decide how relational data becomes text.
    A clear, descriptive template helps the LLM later understand context.
    """
    # Use `.get` to be robust to small schema differences.
    customer_id = row.get("customer_id") or row.get("id") or "unknown"
    name = row.get("customer_name") or row.get("name") or "Unknown Customer"
    city = row.get("city") or row.get("location_city") or row.get("customer_city")
    country = row.get("country") or row.get("customer_country")

    parts: List[str] = []
    parts.append(f"Customer {customer_id}: {name}.")

    if city or country:
        loc_parts = []
        if city:
            loc_parts.append(city)
        if country:
            loc_parts.append(country)
        parts.append("Location: " + ", ".join(loc_parts) + ".")

    # You can extend this with segment, total orders, etc., once you know the schema.

    return " ".join(parts)


def product_row_to_text(row: Dict) -> str:
    """
    Convert a single product row into a short natural language description.

    This uses the optimized V2 schema:
      - product_id
      - product_name
      - actual_price
      - selling_price
      - expiry_date
      - total_quantity (if present)
    """
    product_id = row.get("product_id") or "unknown"
    name = row.get("product_name") or "Unknown Product"
    actual_price = row.get("actual_price")
    selling_price = row.get("selling_price")
    expiry_date = row.get("expiry_date")
    total_quantity = row.get("total_quantity")

    parts: List[str] = []
    parts.append(f"Product {product_id}: {name}.")

    if actual_price is not None and selling_price is not None:
        parts.append(f"Prices: actual price {actual_price}, selling price {selling_price}.")
    elif actual_price is not None:
        parts.append(f"Actual price: {actual_price}.")
    elif selling_price is not None:
        parts.append(f"Selling price: {selling_price}.")

    if expiry_date:
        parts.append(f"Expiry date: {expiry_date}.")

    if total_quantity is not None:
        parts.append(f"Total quantity available: {total_quantity}.")

    return " ".join(parts)


def generic_row_to_text(table_name: str, row: Dict) -> str:
    """
    Fallback converter for arbitrary tables when we don't have a custom template.

    WHY: This lets us quickly get a baseline RAG system working over multiple
    tables, and later we can add tailored converters per table for better quality.
    """
    fields = [f"{key}={value}" for key, value in row.items()]
    return f"Row from table '{table_name}': " + ", ".join(fields)


