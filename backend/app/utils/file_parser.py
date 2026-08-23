"""
File parser utilities for CSV and XLSX datasets.
Safely validates, parses, and normalizes tabular files into Pandas DataFrames.
"""
import os
import re
from pathlib import Path
from typing import Tuple, Optional
import pandas as pd


ALLOWED_EXTENSIONS = {".csv", ".xlsx"}
SUPPORTED_MIME_TYPES = {
    "text/csv",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/octet-stream",
    "text/plain",
}


def sanitize_filename(filename: str) -> str:
    """
    Sanitizes an uploaded filename by stripping path separators and special characters.
    """
    base_name = os.path.basename(filename)
    # Remove any characters that aren't alphanumeric, dots, underscores, or hyphens
    sanitized = re.sub(r"[^a-zA-Z0-9._-]", "_", base_name)
    return sanitized or "dataset"


def validate_file_format(filename: str, content_type: Optional[str] = None) -> Tuple[bool, str, str]:
    """
    Validates file extension and format.
    Returns (is_valid, file_type, error_message).
    """
    if not filename:
        return False, "", "Filename is missing or empty."

    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return (
            False,
            "",
            f"Unsupported file format '{ext}'. Only CSV (.csv) and Excel (.xlsx) files are supported.",
        )

    file_type = "csv" if ext == ".csv" else "xlsx"
    return True, file_type, ""


def parse_csv_file(file_path: str) -> pd.DataFrame:
    """
    Parses a CSV file with automatic encoding detection and delimiter handling.
    """
    try:
        # Try standard UTF-8 first
        df = pd.read_csv(file_path, encoding="utf-8", dtype=object, keep_default_na=True)
    except UnicodeDecodeError:
        try:
            # Fallback to Latin-1 / Windows-1252 for legacy datasets
            df = pd.read_csv(file_path, encoding="latin1", dtype=object, keep_default_na=True)
        except Exception as e:
            raise ValueError(f"Failed to decode CSV file: {str(e)}")
    except pd.errors.EmptyDataError:
        raise ValueError("The uploaded CSV file is empty.")
    except Exception as e:
        raise ValueError(f"Error parsing CSV file: {str(e)}")

    return df


def parse_xlsx_file(file_path: str) -> pd.DataFrame:
    """
    Parses an XLSX spreadsheet using openpyxl engine.
    """
    try:
        df = pd.read_excel(file_path, engine="openpyxl", dtype=object)
    except Exception as e:
        raise ValueError(f"Error parsing XLSX file: {str(e)}")

    if df.empty:
        raise ValueError("The uploaded XLSX spreadsheet contains no data or empty sheets.")

    return df


def load_dataset(file_path: str, file_type: str) -> pd.DataFrame:
    """
    Loads and validates a tabular dataset into a pandas DataFrame.
    Guarantees non-empty structure and converts columns to string headers.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    if os.path.getsize(file_path) == 0:
        raise ValueError("The uploaded file is empty (0 bytes).")

    if file_type == "csv":
        df = parse_csv_file(file_path)
    elif file_type == "xlsx":
        df = parse_xlsx_file(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")

    if df.empty or len(df.columns) == 0:
        raise ValueError("The dataset contains 0 rows or 0 columns.")

    # Clean and stringify column headers without modifying actual names
    df.columns = [str(c).strip() if c is not None else f"Unnamed_{i}" for i, c in enumerate(df.columns)]
    
    return df
