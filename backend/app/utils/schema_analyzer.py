"""
Dynamic schema analyzer for arbitrary industrial tabular datasets.
Analyzes column types, null ratios, cardinality, and probabilistic schema candidate roles
without hardcoding any dataset-specific fields.
"""
import re
from typing import Any, Dict, List, Optional
import pandas as pd
import numpy as np


# Generic keyword heuristics (case-insensitive substring/regex matches)
IDENTIFIER_KEYWORDS = {
    "id", "sku", "code", "part_number", "part_no", "partno", "item_number",
    "item_no", "itemno", "article_no", "mpn", "gtin", "upc", "ean", "serial",
    "model_number", "model_no"
}

PRODUCT_NAME_KEYWORDS = {
    "name", "title", "product", "description", "item_name", "item_title",
    "product_name", "model", "designation", "label"
}

CATEGORY_KEYWORDS = {
    "category", "cat", "class", "family", "type", "group", "hierarchy",
    "segment", "sector", "taxonomy", "sub_category", "subcategory"
}


def _clean_token(col: str) -> str:
    """Standardizes string into clean lower snake_case token for keyword inspection."""
    return re.sub(r"[\W_]+", " ", str(col).lower()).strip()


def infer_column_type(series: pd.Series) -> str:
    """
    Infers generic logical type (numeric, boolean, datetime, text, empty) from a series.
    """
    valid_series = series.dropna()
    if valid_series.empty:
        return "empty"

    # Try numeric conversion
    try:
        pd.to_numeric(valid_series)
        return "numeric"
    except (ValueError, TypeError):
        pass

    # Try boolean conversion
    unique_vals = set(valid_series.astype(str).str.strip().str.lower().unique())
    if unique_vals.issubset({"true", "false", "1", "0", "yes", "no", "t", "f", "y", "n"}):
        return "boolean"

    # Try datetime conversion (only if string length suggests standard dates)
    sample_first = str(valid_series.iloc[0]).strip()
    if len(sample_first) in (10, 19, 23, 24) and any(c in sample_first for c in ("-", "/", ":")):
        try:
            pd.to_datetime(valid_series.iloc[:50], errors="raise")
            return "datetime"
        except (ValueError, TypeError):
            pass

    return "text"


def analyze_schema(df: pd.DataFrame, filename: str = "", file_type: str = "") -> Dict[str, Any]:
    """
    Performs comprehensive schema discovery on arbitrary DataFrames.
    Calculates null rates, uniqueness, type inferences, and generic probabilistic candidate roles.
    """
    row_count, col_count = df.shape
    columns = [str(c) for c in df.columns]

    column_details: Dict[str, Dict[str, Any]] = {}
    numeric_columns: List[str] = []
    text_columns: List[str] = []
    likely_identifier_columns: List[str] = []
    likely_product_name_columns: List[str] = []
    likely_category_columns: List[str] = []

    for col in columns:
        series = df[col]
        total_count = len(series)
        null_count = int(series.isna().sum())
        null_pct = float(round((null_count / total_count) * 100, 2)) if total_count > 0 else 0.0

        non_null_series = series.dropna()
        unique_count = int(non_null_series.nunique())
        non_null_count = len(non_null_series)
        uniqueness_ratio = (
            float(round(unique_count / non_null_count, 4)) if non_null_count > 0 else 0.0
        )

        inferred_type = infer_column_type(series)
        pandas_dtype = str(series.dtype)

        is_numeric = inferred_type == "numeric"
        is_text = inferred_type == "text"

        if is_numeric:
            numeric_columns.append(col)
        elif is_text:
            text_columns.append(col)

        # Get first few non-null sample values safely
        sample_vals = non_null_series.head(5).tolist()
        sample_vals_cleaned = [
            int(x) if isinstance(x, (np.integer, int))
            else float(x) if isinstance(x, (np.floating, float)) and not np.isnan(x)
            else str(x)
            for x in sample_vals
        ]

        # Evaluate generic heuristics for identifier / product name / category
        token = _clean_token(col)
        tokens_set = set(token.split())

        # 1. Identifier Heuristic:
        # High uniqueness ratio (> 0.70) AND has id/code/sku token or exact match
        has_id_keyword = any(k in tokens_set or token.endswith(f" {k}") or token == k for k in IDENTIFIER_KEYWORDS)
        is_likely_identifier = bool(
            (has_id_keyword and uniqueness_ratio > 0.40) or (uniqueness_ratio > 0.95 and total_count > 5)
        )

        # 2. Product Name Heuristic:
        # Text type, moderate-to-high uniqueness, name/title/product/description keywords
        has_name_keyword = any(k in tokens_set or token == k for k in PRODUCT_NAME_KEYWORDS)
        is_likely_product_name = bool(
            has_name_keyword and is_text and not is_likely_identifier and uniqueness_ratio > 0.30
        )

        # 3. Category Heuristic:
        # Categorical column with category keywords, or lower uniqueness in larger datasets
        has_cat_keyword = any(k in tokens_set or token.endswith(f" {k}") or token == k for k in CATEGORY_KEYWORDS)
        is_likely_category = bool(
            has_cat_keyword and is_text and not is_likely_identifier
        )

        if is_likely_identifier:
            likely_identifier_columns.append(col)
        if is_likely_product_name:
            likely_product_name_columns.append(col)
        if is_likely_category:
            likely_category_columns.append(col)

        column_details[col] = {
            "column_name": col,
            "inferred_type": inferred_type,
            "pandas_dtype": pandas_dtype,
            "total_count": total_count,
            "null_count": null_count,
            "null_percentage": null_pct,
            "unique_count": unique_count,
            "uniqueness_ratio": uniqueness_ratio,
            "sample_values": sample_vals_cleaned,
            "is_numeric": is_numeric,
            "is_text": is_text,
            "is_likely_identifier": is_likely_identifier,
            "is_likely_product_name": is_likely_product_name,
            "is_likely_category": is_likely_category,
        }

    return {
        "filename": filename,
        "file_type": file_type,
        "row_count": row_count,
        "column_count": col_count,
        "columns": columns,
        "column_details": column_details,
        "numeric_columns": numeric_columns,
        "text_columns": text_columns,
        "likely_identifier_columns": likely_identifier_columns,
        "likely_product_name_columns": likely_product_name_columns,
        "likely_category_columns": likely_category_columns,
    }


def pick_best_candidate_column(candidates: List[str], column_details: Dict[str, Dict[str, Any]], role: str) -> Optional[str]:
    """
    Selects the single most confident candidate column for master product fields if any exist.
    """
    if not candidates:
        return None

    if len(candidates) == 1:
        return candidates[0]

    # If multiple candidates, rank based on heuristics
    if role == "identifier":
        # Prefer higher uniqueness ratio and cleaner id naming
        return max(candidates, key=lambda c: (
            1.0 if "id" in c.lower() or "sku" in c.lower() or "code" in c.lower() else 0.5,
            column_details[c]["uniqueness_ratio"]
        ))
    elif role == "name":
        # Prefer 'name' or 'title' over 'description'
        return max(candidates, key=lambda c: (
            2.0 if "name" in c.lower() or "title" in c.lower() else 1.0,
            -column_details[c]["null_percentage"]
        ))
    elif role == "category":
        # Prefer lowest null percentage and 'category' exact matches
        return max(candidates, key=lambda c: (
            2.0 if "category" in c.lower() else 1.0,
            -column_details[c]["null_percentage"]
        ))

    return candidates[0]
