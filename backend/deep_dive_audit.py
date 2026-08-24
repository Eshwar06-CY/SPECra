"""
Deep Dive Dimension & Ambiguity Analysis Script.
"""
import json

with open("precision_audit_log.json") as f:
    data = json.load(f)

triple_dims = []
for item in data["dimensions"]["correct"]:
    desc = item["desc"]
    if "x" in desc and desc.count("x") >= 2:
        triple_dims.append(item)

print(f"Found {len(triple_dims)} discs with 3 dimensions (Diameter x Thickness x Arbor):")
for t in triple_dims[:10]:
    print("  Desc:", t["desc"])
    print("    Extracted -> W:", t["extracted_w"], "L:", t["extracted_l"], "from:", t.get("source_text"))
