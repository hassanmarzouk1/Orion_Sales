1. README.md
# Medallion Architecture Data Warehouse Project

## Overview
This project implements a **Medallion Architecture** (Bronze → Silver → Gold) for building a Dimensional Data Warehouse using **Star Schema** design principles from Ralph Kimball's methodology.

**Goal**: Transform raw sales and forecast data into a clean, performant analytics platform optimized for BI tools like Power BI.

### Key Features
- **Medallion Layers**: Bronze (raw), Silver (cleaned), Gold (DWH - Star Schema)
- **Dimensional Modeling**: Star Schema with conformed dimensions
- **SCD Type 2**: On Product dimension to track price history
- **Shrunken Dimension**: `YEAR_DIM` for aggregate facts
- **ETL Pipeline**: Fully scripted in Python + SQLite
- **BI Ready**: Clean relationships, surrogate keys, unknown members (-1)

## Data Model Summary
- **Fact Tables**: `gold_fact_sales` (transactional), `gold_actual_sales_agg_fact`, `gold_forecast`
- **Dimensions**: Product (SCD2), Customer, Location, Date (daily), Year (shrunken)
- **Design Choice**: Star Schema (vs Snowflake) for better query performance and simpler joins.

## Project Structure
Hassan Marzouk Task/
├── data/                    # JSON source files & Data Exploration CSV
├── Scripts/
│   ├── DB.py                # Database setup (Medallion layers)
│   ├── Extractor.py
│   ├── Transformer.py
│   ├── Loader.py
│   ├── Pipeline.py          # Main orchestrator
│   └── Validate.py
|   |__ medallion_arch.db        # SQLite database
├── README.md
├── Documentation.md
└── Sales_Dashboard



## Quick Start

1. **Install dependencies**:
   ```bash
   pip install pandas
   ```

2. Run the full pipeline:Bash
python Scripts/Pipeline.py

3. (Optional) Validate results:
python Scripts/Validate.py

4. Connect Power BI to medallion_arch.db and mark gold_dim_date as Date Table.
