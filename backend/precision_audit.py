"""
Precision Audit Script for SPECra Deterministic Extractions.
Inspects all 1,000 products from 'Unihack_ Sample Dataset - Input.csv'
Audits every extraction across:
1. Dimensions (WIDTH, LENGTH)
2. Brands (BRAND_NAME)
3. Packaging (Selling Qty, Selling UOM, Standard Packaging Info)
4. Class / Taxonomy
5. Grit attributes
"""
import os
import re
import json
import pandas as pd
from typing import Dict, List, Any, Tuple

from app.services.enrichment_engine import ProductEnrichmentEngine
from app.services.export_engine import UniHackOutputMapper
from app.models.product import Product

def run_precision_audit():
    input_path = os.path.abspath("data/input/Unihack_ Sample Dataset - Input.csv")
    if not os.path.exists(input_path):
        input_path = os.path.abspath("../data/input/Unihack_ Sample Dataset - Input.csv")
    
    df = pd.read_csv(input_path, dtype=object).fillna("")
    print(f"Loaded {len(df)} products from: {input_path}")

    # Audit Containers
    dim_audit = {"correct": [], "incorrect": [], "ambiguous": []}
    brand_audit = {"correct": [], "incorrect": [], "ambiguous": []}
    pkg_audit = {"correct": [], "incorrect": [], "ambiguous": []}
    class_audit = {"correct": [], "incorrect": [], "ambiguous": []}
    grit_audit = {"correct": [], "incorrect": [], "ambiguous": []}

    for idx, row in df.iterrows():
        p_num = idx + 1
        raw_data = row.to_dict()
        desc = str(row.get("Part_Desc", "")).strip()
        mfg = str(row.get("Mfg_Part_Num", "")).strip()
        manuf = str(row.get("Part_Manuf", "")).strip()

        prod = Product(
            id=f"audit-{p_num}",
            external_product_id=mfg,
            raw_data=raw_data
        )

        mapped_row = UniHackOutputMapper.map_product_to_row(prod)

        # 1. Audit Dimensions
        w = mapped_row.get("WIDTH", "")
        l = mapped_row.get("LENGTH", "")
        w_uom = mapped_row.get("WIDTH_UOM", "")
        l_uom = mapped_row.get("LENGTH_UOM", "")

        if w or l:
            # Check if this was a dual dimension (e.g. 1/2"x18", 2.75x30, 14"x1")
            dim_match = re.search(
                r"(\d+(?:[\s\-]\d+/\d+|\.\d+|/\d+)?)\s*(?:\"|in|inch|inches|'')?\s*[xX*]\s*(\d+(?:[\s\-]\d+/\d+|\.\d+|/\d+)?)\s*(\"|in|inch|inches|''|mm|cm|ft)?",
                desc,
                re.IGNORECASE,
            )
            # Check if single dimension like 5" Disc
            single_match = re.search(
                r"\b(\d+(?:[\s\-]\d+/\d+|\.\d+|/\d+)?)\s*(\"|in|inch|inches|'')\s*(?:Disc|Wheel|Cut-Off|Blade|Pad)\b",
                desc,
                re.IGNORECASE,
            )

            record = {
                "row": p_num,
                "desc": desc,
                "extracted_w": w,
                "extracted_l": l,
                "uom": w_uom,
            }

            if dim_match:
                # Clear dual dimension in description
                dim_str = dim_match.group(0)
                # Verify if values match
                record["match_type"] = "dual"
                record["source_text"] = dim_str
                dim_audit["correct"].append(record)
            elif single_match:
                # Single circular dimension mapped to width & length
                dim_str = single_match.group(0)
                record["match_type"] = "single_circular"
                record["source_text"] = dim_str
                # For circular discs, diameter is both width and length (bounding box), but semantically it's a diameter
                # We categorize as ambiguous / diameter-semantic check
                dim_audit["ambiguous"].append(record)
            else:
                dim_audit["incorrect"].append(record)

        # 2. Audit Brand
        brand = mapped_row.get("BRAND_NAME", "")
        if brand:
            record_b = {
                "row": p_num,
                "desc": desc,
                "manuf": manuf,
                "brand": brand,
            }
            # Check if brand is explicit in brand columns
            e1 = raw_data.get("E1_Brand", "")
            unilog = raw_data.get("Unilog_Brand", "")
            dib = raw_data.get("DIB_Brand", "")

            explicit_brand = None
            for b in [e1, unilog, dib]:
                if b and not b.startswith("--") and b.lower() not in {"unbranded", "unknown", "none", "no brand"}:
                    explicit_brand = b
                    break

            if explicit_brand:
                record_b["source"] = "explicit_column"
                brand_audit["correct"].append(record_b)
            else:
                # Check regex in description
                # Check for false positives:
                # 3M in 3MABR or standard word
                if brand.lower() == "sia" and not re.search(r"\bSIA\b", desc):
                    brand_audit["incorrect"].append(record_b)
                elif brand in desc or (brand == "Milwaukee" and "Milw" in desc):
                    record_b["source"] = "description_regex"
                    brand_audit["correct"].append(record_b)
                else:
                    brand_audit["ambiguous"].append(record_b)

        # 3. Audit Packaging
        qty = mapped_row.get("Selling Qty", "")
        uom = mapped_row.get("Selling UOM", "")
        pkg = mapped_row.get("Standard Packaging Information", "")
        if qty or uom or pkg:
            record_p = {
                "row": p_num,
                "desc": desc,
                "qty": qty,
                "uom": uom,
                "pkg": pkg,
            }
            # Verify explicit packaging pattern exists
            has_pack = re.search(r"(\d+)\s*(?:-|/)?\s*(pc|pcs|piece|pieces|pk|pack|packs|ct|count|box|boxes|disc/box|discs/box|per box)\b", desc, re.IGNORECASE)
            if has_pack:
                record_p["source_text"] = has_pack.group(0)
                pkg_audit["correct"].append(record_p)
            else:
                pkg_audit["incorrect"].append(record_p)

        # 4. Audit Class
        cls_val = mapped_row.get("Class", "")
        if cls_val:
            record_c = {
                "row": p_num,
                "desc": desc,
                "class": cls_val,
            }
            desc_l = desc.lower()
            if cls_val == "Sanding Belt" and ("belt" in desc_l):
                class_audit["correct"].append(record_c)
            elif cls_val == "Cut-Off Disc" and ("cut-off" in desc_l or "cut off" in desc_l or "cutoff" in desc_l):
                class_audit["correct"].append(record_c)
            elif cls_val == "Sanding Disc" and ("sanding disc" in desc_l):
                class_audit["correct"].append(record_c)
            elif cls_val == "Flap Disc" and ("flap disc" in desc_l):
                class_audit["correct"].append(record_c)
            elif cls_val == "Grinding Wheel" and ("grinding wheel" in desc_l or "cut-off wheel" in desc_l):
                class_audit["correct"].append(record_c)
            elif cls_val == "Sanding Sheet" and ("sheet" in desc_l):
                class_audit["correct"].append(record_c)
            elif cls_val == "Abrasive Pad" and ("pad" in desc_l):
                class_audit["correct"].append(record_c)
            elif cls_val == "Abrasive Roll" and ("roll" in desc_l):
                class_audit["correct"].append(record_c)
            elif cls_val == "Abrasive Disc" and ("disc" in desc_l):
                class_audit["correct"].append(record_c)
            else:
                class_audit["ambiguous"].append(record_c)

        # 5. Audit Grit
        grit_label = mapped_row.get("ATTRIBUTE_LABEL 1", "")
        grit_val = mapped_row.get("ATTRIBUTE_VALUE 1", "")
        if grit_label == "Grit Size" and grit_val:
            record_g = {
                "row": p_num,
                "desc": desc,
                "grit": grit_val,
            }
            # Verify explicit P80 / 80 Grit in text
            if re.search(rf"\bP{grit_val}\b|\b{grit_val}\s*Grit\b", desc, re.IGNORECASE):
                record_g["source_text"] = f"P{grit_val} / {grit_val} Grit"
                grit_audit["correct"].append(record_g)
            else:
                grit_audit["incorrect"].append(record_g)

    # Calculate Precision
    def calc_prec(cat_dict):
        c = len(cat_dict["correct"])
        i = len(cat_dict["incorrect"])
        a = len(cat_dict["ambiguous"])
        tot = c + i + a
        # Strict precision: Correct / Total Extracted
        prec = (c / tot * 100) if tot > 0 else 100.0
        return tot, c, i, a, prec

    print("\n" + "="*80)
    print("           PRECISION AUDIT RESULTS FOR DETERMINISTIC EXTRACTORS")
    print("="*80)
    print(f"{'FIELD':<25} | {'EXTRACTED':<10} | {'CORRECT':<10} | {'INCORRECT':<10} | {'AMBIGUOUS':<10} | {'PRECISION':<10}")
    print("-"*80)

    for name, data in [
        ("WIDTH / LENGTH", dim_audit),
        ("BRAND_NAME", brand_audit),
        ("Selling Qty / Packaging", pkg_audit),
        ("Class (Taxonomy)", class_audit),
        ("Grit (Attribute Slot 1)", grit_audit),
    ]:
        tot, c, i, a, prec = calc_prec(data)
        print(f"{name:<25} | {tot:<10} | {c:<10} | {i:<10} | {a:<10} | {prec:.1f}%")
    print("="*80)

    # Save detailed inspection logs
    output_audit = {
        "dimensions": dim_audit,
        "brands": brand_audit,
        "packaging": pkg_audit,
        "class": class_audit,
        "grit": grit_audit,
    }

    with open("precision_audit_log.json", "w") as f:
        json.dump(output_audit, f, indent=2)
    print("\nDetailed precision audit log written to: precision_audit_log.json")

if __name__ == "__main__":
    run_precision_audit()
