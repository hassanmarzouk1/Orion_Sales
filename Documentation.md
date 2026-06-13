
---

### 2. **`Documentation.md`**

```markdown
# Comprehensive Project Documentation

## 1. Project Objective
Build a robust **Dimensional Data Warehouse** using **Medallion Architecture** to support sales analysis and forecasting comparison.

## 2. Architectural Choices (Kimball + Modern Best Practices)

### 2.1 Star Schema vs Snowflake
- **Chosen: Star Schema**
  - Reason: Better query performance, fewer joins, simpler for BI tools (Power BI/Tableau).
  - Avoids unnecessary complexity and "too many dimensions" in fact tables.
  - Reference: *The Data Warehouse Toolkit* – Chapter 3.

### 2.2 Medallion Architecture
- **Bronze**: Raw data from JSON (landing zone).
- **Silver**: Cleaned, standardized, deduplicated data.
- **Gold**: Star Schema dimensional model (facts + dimensions).

### 2.3 Dimensional Modeling Decisions

#### Conformed Dimensions
- `gold_dim_date` (daily) – Master time dimension.
- `gold_dim_year` – **Shrunken conformed dimension** for yearly aggregates.

#### Slowly Changing Dimensions (SCD)
- **Product_DIM**: SCD Type 2 (tracks `unit_price` and attribute changes).
- **Customer_DIM**: Type 1 (no strong need for history tracking).

#### Unknown Member Handling
- Surrogate key `-1` used in most dimensions.
- **Date_DIM exception**: Avoided NULL date row due to Power BI "gaps in dates" error.

#### Grain Definition
- **Sales Fact**: Transaction grain.
- **Actual Sales Agg Fact** & **Forecast Fact**: Yearly grain by Brand + Country_Region.

### 2.4 A Example of Dead-Letter Pattern for handling corputed records (Commented in Transformer.py)

### 2.5 A Assuming Forecast DataSet is generated from ML Model , So I loaded it directly to the Gold Layer

## 3. ETL Pipeline Scripts Explanation

### 4.1 `DB.py`
- Creates all layers and tables including indexes.

### 4.2 `Extractor.py`
- Loads raw JSON into Bronze layer.

### 4.3 `Transformer.py`
- Cleans and standardizes data (Bronze → Silver).

### 4.4 `Loader.py`
- `load_date_dimension()`: Continuous daily dates.
- `load_year_dimension()`: Shrunken YEAR_DIM.
- `load_product_scd2_dimension()`: SCD2 logic.
- `load_sales_fact()`: Joins with SCD2 date range handling.
- Aggregate_Actual_Sales and Forecast Fact_Tables Loaders.

### 4.5 `Pipeline.py`
- End-to-end orchestration.

## 5. Power BI Considerations
- Mark `gold_dim_date.date` as Date Table.
- Use `YEAR_KEY` for aggregate visuals.

## 6. References
- *The Data Warehouse Toolkit* (Kimball) – Ch3
- *Data Engineering Design Patterns* – Ch2 & 3

---

**Author**: Hassan Marzouk  
**Date**: June 2026
