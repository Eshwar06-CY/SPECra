"""
Normalization utilities for Deadlock Industrial Product Intelligence.
Handles dimension conversions, fraction reductions, pack size extractions,
and engineering unit normalizations deterministically.
"""
import re
from typing import Optional, Tuple


# Fraction mapping
FRACTION_MAP = {
    "1/2": 0.5,
    "1/4": 0.25,
    "3/4": 0.75,
    "1/8": 0.125,
    "3/8": 0.375,
    "5/8": 0.625,
    "7/8": 0.875,
    "1/16": 0.0625,
    "3/16": 0.1875,
    "5/16": 0.3125,
    "7/16": 0.4375,
    "9/16": 0.5625,
    "11/16": 0.6875,
    "13/16": 0.8125,
    "15/16": 0.9375,
    "1/32": 0.03125,
    "1/64": 0.015625,
    "1/3": 0.3333,
    "2/3": 0.6667,
}

# Unit canonical normalization dictionary
UNIT_MAP = {
    # Length
    "\"": "in",
    "in": "in",
    "inch": "in",
    "inches": "in",
    "''": "in",
    "ft": "ft",
    "foot": "ft",
    "feet": "ft",
    "'": "ft",
    "yd": "yd",
    "yard": "yd",
    "mm": "mm",
    "millimeter": "mm",
    "millimeters": "mm",
    "cm": "cm",
    "centimeter": "cm",
    "centimeters": "cm",
    "m": "m",
    "meter": "m",
    "meters": "m",
    # Weight
    "lb": "lbs",
    "lbs": "lbs",
    "pound": "lbs",
    "pounds": "lbs",
    "oz": "oz",
    "ounce": "oz",
    "ounces": "oz",
    "g": "g",
    "gram": "g",
    "grams": "g",
    "kg": "kg",
    "kilogram": "kg",
    "kilograms": "kg",
    # Packaging / Quantity
    "pc": "pieces",
    "pcs": "pieces",
    "piece": "pieces",
    "pieces": "pieces",
    "pk": "pieces",
    "pack": "pieces",
    "packs": "pieces",
    "count": "pieces",
    "ct": "pieces",
    "ea": "each",
    "each": "each",
    "box": "box",
    "boxes": "box",
    "set": "set",
    "sets": "set",
    "pair": "pair",
    "pairs": "pair",
    "roll": "roll",
    "rolls": "roll",
    # Electrical & Power
    "v": "V",
    "volt": "V",
    "volts": "V",
    "a": "A",
    "amp": "A",
    "amps": "A",
    "w": "W",
    "watt": "W",
    "watts": "W",
    "kw": "kW",
    "kilowatt": "kW",
    "hp": "HP",
    "horsepower": "HP",
    "hz": "Hz",
    "hertz": "Hz",
    "rpm": "RPM",
    # Pressure
    "psi": "PSI",
    "bar": "bar",
}


def normalize_unit(unit_str: Optional[str]) -> Optional[str]:
    """
    Normalizes arbitrary unit strings to standard engineering representations.
    E.g., 'inches' -> 'in', 'pcs' -> 'pieces', 'volts' -> 'V'.
    """
    if not unit_str:
        return None
    cleaned = str(unit_str).strip().lower().replace(".", "")
    return UNIT_MAP.get(cleaned, unit_str.strip())


def normalize_numeric_string(val_str: Optional[str]) -> Optional[str]:
    """
    Normalizes mixed numbers and fractions to standardized decimal strings.
    E.g., '1 1/2' -> '1.5', '1/2' -> '0.5', '18' -> '18'.
    """
    if not val_str:
        return None
    cleaned = str(val_str).strip()

    # Case 1: Simple integer or float
    try:
        f = float(cleaned)
        if f.is_integer():
            return str(int(f))
        return f"{f:.4f}".rstrip("0").rstrip(".")
    except ValueError:
        pass

    # Case 2: Mixed number, e.g. "1 1/2" or "1-1/2"
    mixed_match = re.match(r"^(\d+)[\s\-]+(\d+/\d+)$", cleaned)
    if mixed_match:
        whole = int(mixed_match.group(1))
        frac_str = mixed_match.group(2)
        if frac_str in FRACTION_MAP:
            total = whole + FRACTION_MAP[frac_str]
            return f"{total:.4f}".rstrip("0").rstrip(".")
        try:
            num, denom = map(int, frac_str.split("/"))
            if denom != 0:
                total = whole + (num / denom)
                return f"{total:.4f}".rstrip("0").rstrip(".")
        except Exception:
            pass

    # Case 3: Simple fraction, e.g. "1/2", "3/4"
    if cleaned in FRACTION_MAP:
        return str(FRACTION_MAP[cleaned])
    frac_match = re.match(r"^(\d+)/(\d+)$", cleaned)
    if frac_match:
        num, denom = int(frac_match.group(1)), int(frac_match.group(2))
        if denom != 0:
            total = num / denom
            return f"{total:.4f}".rstrip("0").rstrip(".")

    return cleaned


def parse_measurement(text: str) -> Optional[Tuple[str, str, str]]:
    """
    Parses a measurement token like '1/2\"', '18 in', '6pc' into:
    (raw_value, normalized_value, canonical_unit).
    """
    if not text:
        return None
    cleaned = text.strip()

    # Pattern for Dimension: number/fraction + unit (e.g. 1/2", 18in, 1-1/2 in)
    dim_match = re.search(r"(\d+(?:[\s\-]\d+/\d+|\.\d+|/\d+)?)\s*(\"|''|in(?:ch(?:es)?)?|mm|cm|m|ft|feet|lbs?|oz|pcs?|pieces?|pk|pack)", cleaned, re.IGNORECASE)
    if dim_match:
        val_part = dim_match.group(1)
        unit_part = dim_match.group(2)
        norm_val = normalize_numeric_string(val_part)
        norm_uom = normalize_unit(unit_part)
        return (val_part, norm_val, norm_uom)

    return None
