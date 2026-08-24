# SPECra — Official Judge & Evaluator Demonstration Guide

> **Product**: SPECra (*"AI-Powered Product Intelligence for Industrial Commerce"*)  
> **Team**: Team DEADLOCK (Eshwar M & Granthini CA)  
> **Event**: UniHack 2026  
> **Evaluation Duration**: ~3 to 5 Minutes  
> **Target Dataset**: `data/input/Unihack_ Sample Dataset - Input.csv` (1,000 Products, 6 Source Columns)

---

## 1. Quick Start / One-Click Demo Setup

### Step 1: Start Backend Core Engine
Open PowerShell in project root:
```powershell
cd D:\Antigravity_Projects\deadlock\backend
..\venv\Scripts\Activate.ps1
uvicorn app.main:app --port 8000 --reload
```

### Step 2: Start Frontend Web Interface
Open a second PowerShell terminal:
```powershell
cd D:\Antigravity_Projects\deadlock\frontend
npm run dev
```
Navigate to: `http://localhost:5173`

---

## 2. Recommended 7-Step Demonstration Flow

```
[1] Landing Page   →   [2] Ingestion   →   [3] NL Query Planner   →   [4] Analysis Pipeline
                                                                               │
[7] 252-Col Export  ←   [6] Quality Review  ←   [5] Results & Drawer  ←────────┘
```

### Step 1: Landing Page & Purpose (0:00 - 0:30)
- **What to Observe**:
  - Clean industrial dark aesthetic with brand identity (*"SPECra"* by *Team DEADLOCK*).
  - Clear value proposition: *"Turn messy product data into intelligence."*
  - Click **"Start with your catalog"** or **"Sign In"**.

---

### Step 2: Catalog Upload & Instant Schema Discovery (0:30 - 1:00)
- **Action**: In the Upload zone, select or drag-and-drop:
  `D:\Antigravity_Projects\deadlock\data\input\Unihack_ Sample Dataset - Input.csv`
- **What to Observe**:
  - Automatic file format and size validation.
  - Ingestion Summary: **1,000 Products**, **6 Source Columns** (`Mfg_Part_Num`, `Part_Desc`, `E1_Brand`, `Unilog_Brand`, `DIB_Brand`, `Part_Manuf`).
  - Click **"Continue to Requirements"**.

---

### Step 3: Natural-Language Requirement Definition (1:00 - 1:45)
- **Action**: In the Query Planner textarea, type (or click an example prompt):
  > *"Find sanding products and show their manufacturer, brand, product name, dimensions, grit and packaging information."*
- **Action**: Click **"Interpret Request"**.
- **What to Observe**:
  - **Interpreted Request**: Filter detected (`category: Sanding / Abrasives`).
  - **Fields to Extract**: `manufacturer`, `brand`, `product_name`, `dimensions`, `grit`, `pack_quantity`, `selling_uom`.
  - **Available vs Unavailable Information**: Highlights what source catalog supports vs what requires inference.
  - Click **"Confirm & Run Analysis"**.

---

### Step 4: 5-Stage Live Processing Pipeline (1:45 - 2:15)
- **What to Observe**:
  - Live progress stepper through 5 discrete processing phases:
    1. *Reading catalog*
    2. *Understanding products* (Gemini AI + deterministic parsing)
    3. *Enriching information* (252-column schema mapping, physical dimensions)
    4. *Validating data* (Unit normalization, anomaly checks)
    5. *Preparing results*
  - 1,000 products processed in **<2 seconds**.

---

### Step 5: Interactive Results Table & Product Drawer (2:15 - 3:00)
- **What to Observe in Table**:
  - Paginated table showing structured attributes with instant search and column sorting.
  - Fast responsive filtering (60 FPS).
- **Action**: Click on any product row (e.g. `3M 775L Stikit Film P120` or `Mirka HIOLIT 5" P80`).
- **What to Observe in Inspection Drawer**:
  - **Overview**: Identity, manufacturer, brand, MPN.
  - **Specifications**: Physical diameter (`5 in`), grit (`P80` / `P120`), abrasive backing.
  - **Packaging**: Pack quantity (`50`), selling unit (`Box`), packaging description.
  - **Provenance Badging**: Clear distinction between:
    - `From catalog` (Direct source quote)
    - `Derived from catalog` (Deterministic normalization / inference)
  - **Source Evidence Tab**: Complete provenance trail showing exact text snippets used to justify each extracted value.

---

### Step 6: 5-Pillar Data Quality Review (3:00 - 3:45)
- **Action**: Click **"Quality Review"** or **"Verified 100%"** badge.
- **What to Observe**:
  - **Quality Score**: Detailed score calculation with 0 critical anomalies.
  - **5 Quality Pillars**:
    1. *Identity*: MPN, Manufacturer, Brand reconciliation.
    2. *Specifications*: Dimension consistency, physical attributes.
    3. *Units & UOM*: Standardized imperial/metric units.
    4. *Evidence*: 100% anchored traceability.
    5. *Consistency*: Zero conflicting attributes across catalog rows.

---

### Step 7: 252-Column Commerce-Ready Export (3:45 - 4:30)
- **Action**: Navigate to **"Export"**.
- **What to Observe**:
  - Export Readiness Summary: **1,000 Products**, **252 Standardized Columns**, **Schema 100% Verified**.
  - Live preview of top columns and rows.
- **Action**: Click **"Download CSV"** or **"Download Excel"** under *UniHack Delivery Format*.
- **Validation**:
  - Downloaded CSV/XLSX file opens cleanly.
  - Contains all **252 exact columns** matching `Unihack_ Expected Output - Delivery Format.csv`.
  - Zero formula injection risks (`=`, `+`, `-`, `@` safely escaped).

---

## 3. Recommended Test Prompts for Judges

| Evaluation Goal | Recommended Prompt | Expected Planner Behavior |
| :--- | :--- | :--- |
| **Complete Industrial Extraction** | *"Find sanding products and show their manufacturer, brand, product name, dimensions, grit and packaging information."* | Extracts 7 canonical fields with dimensions, grit, and pack size. |
| **Brand-Specific Search** | *"Show me all 3M products with part numbers and standard packaging."* | Filters to `brand == 3M`, populates MPN and pack quantity. |
| **Fine Grit Abrasives** | *"Find abrasive discs with grit finer than P150."* | Identifies grit numbers (`P180`, `P220`, `P320`) and filters matching discs. |
| **Package Sizing** | *"Find products sold in packs of 50 or boxes."* | Filters by `Selling Qty == 50` and `Selling UOM == Box`. |
