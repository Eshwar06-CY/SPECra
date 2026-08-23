# SPECra — User Manual

> **Product intelligence, without the data chaos.**  
> A complete, step-by-step guide for non-technical users, catalog managers, and data analysts.

---

## 1. Welcome to SPECra

Industrial product spreadsheets are often messy, incomplete, and difficult to use. Important specifications like width, length, packaging quantity, and part numbers are often tangled inside long descriptions, written in inconsistent units, or missing altogether.

**SPECra turns your messy catalog spreadsheets into clean, structured, and validated product intelligence.**

You don't need any programming skills, database knowledge, or AI expertise. You simply upload your catalog file, describe what information you need in plain English, and SPECra does the hard work for you.

---

## 2. Before You Start

### Supported File Formats
You can upload:
- **CSV files** (`.csv`) — comma-separated or tab-separated text files.
- **Excel spreadsheets** (`.xlsx` or `.xls`).

### What Makes a Good Input File?
- **No manual pre-cleaning needed**: You do **not** need to manually format column names or fix typos before uploading. SPECra automatically understands column semantics.
- **Useful columns to include**: Product descriptions, manufacturer part numbers (MPN), vendor names, item codes, and existing specification columns.
- **File size**: Standard catalog uploads up to 50MB are supported.

---

## 3. Account & Login

1. **Sign Up / Sign In**:
   - Open SPECra in your browser at `http://localhost:5173`.
   - Click **Sign In** in the top navigation bar.
   - Enter your work email and password, or use the pre-configured demo account to explore immediately.
2. **Workspace Privacy**:
   - Your account is isolated in its own private workspace. Your uploaded catalogs, results, and exports can never be seen by other users.

---

## 4. Navigating Your Dashboard

When you log in, your **Dashboard** provides a high-level overview:
- **Catalog Statistics**: Total products processed, average data quality score, and fill rate.
- **Recent Catalogs**: List of previously uploaded spreadsheets with their processing status.
- **New Analysis**: The primary button to start analyzing a new catalog file.

---

## 5. Step-by-Step Workflow

```mermaid
flowchart LR
    Upload[1. Upload Catalog] --> Understand[2. Review Structure]
    Understand --> Req[3. Define Requirements]
    Req --> Process[4. AI & Normalization]
    Process --> Results[5. Inspect Results]
    Results --> Quality[6. Check Quality Score]
    Quality --> Export[7. Download Export]
```

### Step 1: Upload Your Catalog
1. Click **New Analysis** or navigate to **Upload** from the sidebar.
2. Drag and drop your CSV/Excel file into the upload zone, or click **Browse Files**.
3. SPECra will upload the file and immediately scan its contents.

### Step 2: Review Detected Structure
SPECra will display an automatic summary of your catalog:
- Total number of rows and columns.
- Identified product name, identifier, and category columns.
- Click **Continue to Requirements** once reviewed.

### Step 3: Define What You Need in Plain English
Type your requirement in the natural-language prompt box.

#### Writing Effective Prompts:
| ❌ Vague / Ineffective Prompts | ✅ Clear / High-Quality Prompts |
| :--- | :--- |
| *"Give me products."* | *"Find all abrasive products and extract manufacturer, brand, dimensions, and pack quantity."* |
| *"Get everything."* | *"Extract width, length, grit size, manufacturer part number, and packaging quantity."* |
| *"Show sanding items."* | *"Find 3M sanding discs and extract diameter, backing material, package count, and MPN."* |

#### More Example Prompts You Can Try:
- *"Extract product name, manufacturer, brand, width, length, and selling quantity for all belts."*
- *"Find Diablo cutting accessories and extract diameter, arbor size, teeth count, and part number."*
- *"List all items with brand, manufacturer, part description, and unit of measure."*

### Step 4: Run Analysis
Click **Start Analysis**. SPECra will:
1. Extract structured specifications from unstructured text.
2. Convert mixed fractions (e.g. `1/2"`) into standardized decimals (`0.5 in`).
3. Standardize packaging information (e.g. `6pc` &rarr; `6 pieces`).
4. Link every single extracted value back to its exact raw source quote.

### Step 5: Review Results & Traceable Evidence
Once processing finishes, your structured product table appears:
- **Search & Filter**: Search by product name, brand, or part number.
- **Inspect Product**: Click the **Inspect** button on any row to open the **Evidence Drawer**.
  - **Found Directly in Catalog**: Values that were explicitly present in a dedicated column.
  - **Derived from Catalog**: Values intelligent algorithms extracted from unstructured description sentences.
  - **Source Quote**: The exact snippet of text from which the specification was derived.

### Step 6: Check Data Quality & Validation
Click **Quality & Validation** in the navigation bar to inspect your catalog's health score:
- **Score (0–100)**: Overall reliability index computed across all attributes.
- **Identity Check**: Confirms product title, brand, and MPN are complete.
- **Physical Sanity**: Verifies that dimensional units (inches, mm, lbs) make physical sense.
- **Issues List**: View any missing required fields or conflicting manufacturer names.

### Step 7: Export Your Standardized Data
Navigate to **Export**:
1. **Export Preview**: See a live preview of the generated dataset and column fill rates.
2. **Choose Your Format**:
   - **Download CSV**: Standard comma-separated format for quick sharing and importing.
   - **Download Excel (.xlsx)**: Formatted spreadsheet with preserved column widths.
   - **UniHack 252-Column Standard**: Full enterprise format covering 252 authoritative industrial commerce headers.

---

## 6. Understanding SPECra Terminology

### What is "Direct" vs. "Derived"?
- **`DIRECT`**: The value was found explicitly in a dedicated column (e.g., a column labeled `Part_Manuf` containing `3M Corp`).
- **`DERIVED`**: The value was extracted and normalized from a sentence or combined string (e.g., extracting `Width = 0.5 in` from `Part_Desc = '1/2"x18" Sanding Belt'`).

### What Does Fraction Normalization Mean?
Industrial spreadsheets use many different ways to write the same measurement:
- `1/2"` &rarr; Normalized to `0.5 in`
- `1-1/2 in` &rarr; Normalized to `1.5 in`
- `3/4 inch` &rarr; Normalized to `0.75 in`

SPECra standardizes all of these into clean numeric values and consistent unit of measure (UOM) tags.

### Why Are Some Fields Blank?
SPECra follows a strict **No-Hallucination Policy**. If a product description does not mention a specification (for example, voltage for a non-electric hand tool), SPECra **leaves the field blank** rather than guessing or fabricating numbers.

---

## 7. Common User Mistakes & How to Avoid Them

1. **Entering very vague requirements**:
   - *Mistake*: Typing *"products"* or *"fix data"*.
   - *Fix*: Specify the product category and the exact fields you want (e.g., *"Find abrasive discs and extract diameter, grit, and manufacturer"*).
2. **Assuming blank cells mean errors**:
   - *Mistake*: Expecting 100% of the 252 columns to be filled for every product.
   - *Fix*: Industrial products only have relevant attributes (a sanding belt has width/length, but not horsepower). Blank unapplicable columns are completely normal.
3. **Exporting without reviewing the quality score**:
   - *Mistake*: Downloading files immediately without checking validation.
   - *Fix*: Take 30 seconds to review the Quality score and check any highlighted warnings.

---

## 8. Frequently Asked Questions (FAQ)

#### Q1: What types of files can I upload?
**A:** You can upload CSV (`.csv`) and Microsoft Excel spreadsheets (`.xlsx` or `.xls`) up to 50MB.

#### Q2: Does SPECra make up or hallucinate missing information?
**A:** No. SPECra strictly extracts and derives attributes only when evidence exists in your uploaded file. Unsupported fields remain blank.

#### Q3: How does SPECra handle different units of measure?
**A:** SPECra detects units (e.g. inches, mm, feet, lbs, pack counts) and splits them into standard value and unit-of-measure columns (e.g. `WIDTH = 0.5`, `WIDTH_UOM = in`).

#### Q4: Can I search through my processed catalog?
**A:** Yes. The Results page features real-time search across product names, brands, part numbers, and extracted attributes.

#### Q5: What is the 252-column UniHack format?
**A:** It is a standardized industrial commerce catalog schema containing 252 specific headers (including product identity, packaging, dimensional parameters, and dynamic attribute slots).

#### Q6: Can I export my data as a standard Excel file?
**A:** Yes. You can download your processed catalog as an Excel `.xlsx` workbook or a `.csv` file with one click.

#### Q7: Can other users see my uploaded catalogs?
**A:** No. Every user account has an isolated workspace. Your files, jobs, and exports are private to your account.

#### Q8: What should I do if the AI analysis shows "temporarily unavailable"?
**A:** This usually indicates a temporary network timeout or rate limit with the AI service. Click **Retry** on the processing screen.

#### Q9: What does the Quality Score represent?
**A:** The Quality Score (0–100) measures identity completeness (brand, title, MPN), unit validity, dimensional sanity, and evidence consistency across your catalog.

#### Q10: Can I re-run analysis with different requirements?
**A:** Yes. You can enter a new requirement prompt at any time to extract different attributes or filter different categories.

---

## 9. One-Page Quick Start Checklist

- [ ] **1. Sign In**: Log in to your SPECra workspace.
- [ ] **2. Upload**: Go to **New Analysis** and drop your catalog CSV or Excel file.
- [ ] **3. Review Structure**: Confirm detected columns on the Catalog Structure screen.
- [ ] **4. Describe Needs**: Enter your prompt (e.g., *"Extract brand, MPN, dimensions, and packaging"*).
- [ ] **5. Process**: Click **Start Analysis** and let SPECra extract and normalize data.
- [ ] **6. Inspect Evidence**: Click **Inspect** on any product to view source quotes and direct vs. derived badges.
- [ ] **7. Validate**: Review the Quality score and physical sanity audit.
- [ ] **8. Export**: Click **Download CSV** or **Download Excel** to receive your standardized catalog.
