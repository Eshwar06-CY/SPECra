"""
Unit and integration tests for Deadlock Dynamic Data Ingestion Engine.
Covers:
- CSV parsing
- XLSX parsing
- Schema analysis & generic heuristics
- Empty dataset handling
- Unsupported file types
- Missing values handling
- Complete raw_data preservation
"""
import io
import os
import tempfile
import unittest
import uuid
import pandas as pd
import openpyxl

from app.utils.file_parser import (
    sanitize_filename,
    validate_file_format,
    load_dataset,
    parse_csv_file,
    parse_xlsx_file,
)
from app.utils.schema_analyzer import (
    analyze_schema,
    infer_column_type,
    pick_best_candidate_column,
)


class TestFileParser(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_filename_sanitization(self):
        raw = "../../../malicious/path/valve_#123;spec(test).csv"
        sanitized = sanitize_filename(raw)
        self.assertNotIn("/", sanitized)
        self.assertNotIn("..", sanitized)
        self.assertTrue(sanitized.endswith(".csv"))

    def test_validate_file_format(self):
        valid_csv, t_csv, _ = validate_file_format("dataset.csv")
        self.assertTrue(valid_csv)
        self.assertEqual(t_csv, "csv")

        valid_xlsx, t_xlsx, _ = validate_file_format("data.xlsx")
        self.assertTrue(valid_xlsx)
        self.assertEqual(t_xlsx, "xlsx")

        invalid_pdf, _, err = validate_file_format("document.pdf")
        self.assertFalse(invalid_pdf)
        self.assertIn("Unsupported file format", err)

        invalid_empty, _, _ = validate_file_format("")
        self.assertFalse(invalid_empty)

    def test_csv_parsing_and_raw_preservation(self):
        csv_path = os.path.join(self.temp_dir.name, "industrial_valves.csv")
        csv_content = (
            "PartNumber,ValveType,MaxPressure_PSI,Temperature_C,SupplierNotes\n"
            "VLV-1001,Ball Valve,1500,250,High corrosion resistance\n"
            "VLV-1002,Gate Valve,2000,,Standard seal\n"
            "VLV-1003,Check Valve,,400,Cryogenic rated\n"
        )
        with open(csv_path, "w", encoding="utf-8") as f:
            f.write(csv_content)

        df = load_dataset(csv_path, "csv")
        self.assertEqual(len(df), 3)
        self.assertEqual(len(df.columns), 5)
        self.assertIn("PartNumber", df.columns)
        self.assertIn("SupplierNotes", df.columns)
        # Check missing value in row 2 for MaxPressure_PSI
        self.assertTrue(pd.isna(df.loc[2, "MaxPressure_PSI"]))

    def test_xlsx_parsing(self):
        xlsx_path = os.path.join(self.temp_dir.name, "bearings.xlsx")
        df_source = pd.DataFrame({
            "Bearing_SKU": ["BRG-01", "BRG-02", "BRG-03"],
            "Inner_Diameter_mm": [15.0, 20.0, 25.0],
            "Load_Rating_kN": [12.5, 18.2, 22.0],
            "Lubrication": ["Grease", "Oil", "Grease"]
        })
        df_source.to_excel(xlsx_path, index=False, engine="openpyxl")

        df = load_dataset(xlsx_path, "xlsx")
        self.assertEqual(len(df), 3)
        self.assertEqual(list(df.columns), ["Bearing_SKU", "Inner_Diameter_mm", "Load_Rating_kN", "Lubrication"])
        self.assertEqual(str(df.loc[0, "Bearing_SKU"]), "BRG-01")

    def test_empty_dataset_rejection(self):
        empty_csv = os.path.join(self.temp_dir.name, "empty.csv")
        with open(empty_csv, "w", encoding="utf-8") as f:
            f.write("")

        with self.assertRaises(ValueError):
            load_dataset(empty_csv, "csv")


class TestSchemaAnalyzer(unittest.TestCase):

    def test_dynamic_schema_analysis_and_heuristics(self):
        df = pd.DataFrame({
            "item_sku": ["SKU-A1", "SKU-B2", "SKU-C3", "SKU-D4"],
            "product_title": ["Hydraulic Pump 5HP", "Rotary Actuator", "Pneumatic Valve", "Servo Motor"],
            "product_category": ["Pumps", "Actuators", "Valves", "Motors"],
            "operating_voltage": [220, 240, 24, 480],
            "notes": ["Heavy duty", None, "Silent operation", "Explosion proof"]
        })

        analysis = analyze_schema(df, filename="components.csv", file_type="csv")

        self.assertEqual(analysis["row_count"], 4)
        self.assertEqual(analysis["column_count"], 5)
        self.assertIn("item_sku", analysis["likely_identifier_columns"])
        self.assertIn("product_title", analysis["likely_product_name_columns"])
        self.assertIn("product_category", analysis["likely_category_columns"])
        self.assertIn("operating_voltage", analysis["numeric_columns"])
        self.assertIn("product_title", analysis["text_columns"])

        # Check null rates
        notes_details = analysis["column_details"]["notes"]
        self.assertEqual(notes_details["null_count"], 1)
        self.assertEqual(notes_details["null_percentage"], 25.0)

    def test_type_inference(self):
        num_s = pd.Series(["100", "200.5", "300"])
        self.assertEqual(infer_column_type(num_s), "numeric")

        text_s = pd.Series(["Stainless Steel 316", "Brass Alloy", "Titanium"])
        self.assertEqual(infer_column_type(text_s), "text")

        bool_s = pd.Series(["true", "false", "true"])
        self.assertEqual(infer_column_type(bool_s), "boolean")

        empty_s = pd.Series([None, None])
        self.assertEqual(infer_column_type(empty_s), "empty")

    def test_arbitrary_unstructured_schema(self):
        # Test with random arbitrary domain without typical naming
        df = pd.DataFrame({
            "alpha_code": ["X1", "X2", "X3"],
            "weight_kg": [10.5, 20.1, 30.0],
            "custom_flag": ["yes", "no", "yes"]
        })
        analysis = analyze_schema(df, filename="custom.csv", file_type="csv")
        self.assertEqual(analysis["row_count"], 3)
        self.assertEqual(len(analysis["columns"]), 3)
        # Should not crash on arbitrary schemas
        self.assertIn("weight_kg", analysis["numeric_columns"])


if __name__ == "__main__":
    unittest.main()
