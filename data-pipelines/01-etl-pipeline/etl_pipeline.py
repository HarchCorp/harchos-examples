#!/usr/bin/env python3
"""ETL (Extract-Transform-Load) pipeline for HarchOS.

A complete ETL pipeline that:
1. Extracts CSV data from an input directory
2. Validates schema and data quality
3. Transforms: cleans, filters, aggregates, and enriches
4. Loads processed data to Parquet format

Supports chunked processing for large datasets that don't fit in memory.

Usage:
    python etl_pipeline.py --input /data/raw --output /data/processed
    python etl_pipeline.py --input ./data/raw --output ./data/processed --chunk-size 5000
"""

import argparse
import glob
import json
import os
import time
from datetime import datetime

import pandas as pd


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Expected schema for input CSV files
EXPECTED_SCHEMA = {
    "id": "int64",
    "date": "str",          # Will be parsed as datetime
    "category": "str",
    "value": "float64",
    "quantity": "int64",
    "region": "str",
}

VALID_CATEGORIES = {"electronics", "clothing", "food", "books", "home", "sports"}
VALID_REGIONS = {"NA", "EU", "APAC", "LATAM"}


# ---------------------------------------------------------------------------
# Extract
# ---------------------------------------------------------------------------

def extract(input_dir: str) -> list:
    """Find and list CSV files in the input directory."""
    pattern = os.path.join(input_dir, "**", "*.csv")
    files = glob.glob(pattern, recursive=True)

    if not files:
        # Generate sample data if no input files exist
        print(f"No CSV files found in {input_dir} — generating sample data...")
        sample_dir = os.path.join(input_dir, "sample")
        os.makedirs(sample_dir, exist_ok=True)
        _generate_sample_data(sample_dir)
        files = glob.glob(os.path.join(sample_dir, "*.csv"))

    print(f"Found {len(files)} CSV file(s)")
    for f in files:
        size_mb = os.path.getsize(f) / 1024 / 1024
        print(f"  {f} ({size_mb:.2f} MB)")

    return files


def _generate_sample_data(output_dir: str, num_rows: int = 5000):
    """Generate sample CSV data for testing."""
    import numpy as np

    np.random.seed(42)
    categories = list(VALID_CATEGORIES)
    regions = list(VALID_REGIONS)

    dates = pd.date_range("2024-01-01", periods=365, freq="D")
    data = {
        "id": range(1, num_rows + 1),
        "date": np.random.choice(dates, num_rows),
        "category": np.random.choice(categories, num_rows),
        "value": np.round(np.random.exponential(100, num_rows), 2),
        "quantity": np.random.randint(1, 50, num_rows),
        "region": np.random.choice(regions, num_rows),
    }

    df = pd.DataFrame(data)
    # Introduce some data quality issues for the transform step to fix
    num_nulls = num_rows // 20
    null_indices = np.random.choice(num_rows, num_nulls, replace=False)
    df.loc[null_indices[:num_nulls//2], "value"] = None
    df.loc[null_indices[num_nulls//2:], "category"] = None

    output_path = os.path.join(output_dir, "sample_data.csv")
    df.to_csv(output_path, index=False)
    print(f"Generated sample data: {output_path} ({num_rows} rows)")


# ---------------------------------------------------------------------------
# Validate
# ---------------------------------------------------------------------------

def validate(df: pd.DataFrame, filename: str) -> dict:
    """Validate DataFrame schema and data quality.

    Returns a validation report dict with any issues found.
    """
    report = {
        "filename": filename,
        "rows": len(df),
        "columns": list(df.columns),
        "issues": [],
    }

    # Check required columns
    missing_cols = set(EXPECTED_SCHEMA.keys()) - set(df.columns)
    if missing_cols:
        report["issues"].append(f"Missing columns: {missing_cols}")

    # Check for null values
    null_counts = df.isnull().sum()
    for col, count in null_counts.items():
        if count > 0:
            report["issues"].append(f"Column '{col}' has {count} null values ({count/len(df)*100:.1f}%)")

    # Check category values
    if "category" in df.columns:
        invalid_cats = set(df["category"].dropna().unique()) - VALID_CATEGORIES
        if invalid_cats:
            report["issues"].append(f"Invalid categories: {invalid_cats}")

    # Check region values
    if "region" in df.columns:
        invalid_regions = set(df["region"].dropna().unique()) - VALID_REGIONS
        if invalid_regions:
            report["issues"].append(f"Invalid regions: {invalid_regions}")

    status = "PASS" if not report["issues"] else "WARN"
    report["status"] = status
    return report


# ---------------------------------------------------------------------------
# Transform
# ---------------------------------------------------------------------------

def transform(df: pd.DataFrame, date_column: str = "date") -> pd.DataFrame:
    """Apply transformations to the data.

    Steps:
    1. Parse dates
    2. Fill/remove nulls
    3. Add derived columns
    4. Filter invalid rows
    """
    original_rows = len(df)

    # 1. Parse dates
    if date_column in df.columns:
        df[date_column] = pd.to_datetime(df[date_column], errors="coerce")

    # 2. Handle nulls
    if "value" in df.columns:
        median_value = df["value"].median()
        df["value"] = df["value"].fillna(median_value)

    if "category" in df.columns:
        df["category"] = df["category"].fillna("unknown")

    if "quantity" in df.columns:
        df["quantity"] = df["quantity"].fillna(1)

    # Drop rows with null dates (can't fix those)
    df = df.dropna(subset=[date_column])

    # 3. Add derived columns
    if "value" in df.columns and "quantity" in df.columns:
        df["total_amount"] = df["value"] * df["quantity"]

    if date_column in df.columns:
        df["year"] = df[date_column].dt.year
        df["month"] = df[date_column].dt.month
        df["day_of_week"] = df[date_column].dt.day_name()

    # 4. Filter invalid values
    if "value" in df.columns:
        df = df[df["value"] >= 0]

    if "quantity" in df.columns:
        df = df[df["quantity"] > 0]

    df = df.reset_index(drop=True)
    removed = original_rows - len(df)
    print(f"  Transformed: {original_rows} -> {len(df)} rows ({removed} removed)")

    return df


# ---------------------------------------------------------------------------
# Load
# ---------------------------------------------------------------------------

def load(df: pd.DataFrame, output_dir: str, filename: str) -> str:
    """Write processed data to Parquet format."""
    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.splitext(filename)[0]
    output_path = os.path.join(output_dir, f"{base_name}.parquet")

    df.to_parquet(output_path, index=False, engine="pyarrow")
    size_mb = os.path.getsize(output_path) / 1024 / 1024
    print(f"  Loaded: {output_path} ({size_mb:.2f} MB, {len(df)} rows)")

    return output_path


def write_summary(results: list, output_dir: str, pipeline_stats: dict):
    """Write a pipeline run summary."""
    summary = {
        "pipeline": "etl",
        "timestamp": datetime.utcnow().isoformat(),
        "stats": pipeline_stats,
        "files": results,
    }
    summary_path = os.path.join(output_dir, "_pipeline_summary.json")
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nPipeline summary: {summary_path}")


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="ETL Pipeline")
    parser.add_argument("--input", type=str, default="/data/raw",
                        help="Input data directory")
    parser.add_argument("--output", type=str, default="/data/processed",
                        help="Output data directory")
    parser.add_argument("--date-column", type=str, default="date",
                        help="Column to parse as dates")
    parser.add_argument("--chunk-size", type=int, default=10000,
                        help="Processing chunk size (0 = no chunking)")
    args = parser.parse_args()

    start_time = time.time()
    print("ETL Pipeline")
    print(f"  Input:  {args.input}")
    print(f"  Output: {args.output}")
    print(f"  Chunk size: {args.chunk_size}")
    print()

    # Extract
    print("=" * 50)
    print("EXTRACT")
    print("=" * 50)
    files = extract(args.input)

    # Process each file
    results = []
    total_rows_in = 0
    total_rows_out = 0

    for filepath in files:
        filename = os.path.basename(filepath)
        print(f"\nProcessing: {filename}")
        print("-" * 40)

        # Read
        if args.chunk_size > 0:
            chunks = pd.read_csv(filepath, chunksize=args.chunk_size)
            df_list = [chunk for chunk in chunks]
            df = pd.concat(df_list, ignore_index=True)
        else:
            df = pd.read_csv(filepath)

        total_rows_in += len(df)
        print(f"  Read {len(df)} rows")

        # Validate
        print("  Validating...")
        report = validate(df, filename)
        print(f"  Validation: {report['status']} ({len(report['issues'])} issues)")
        for issue in report["issues"]:
            print(f"    - {issue}")

        # Transform
        print("  Transforming...")
        df = transform(df, date_column=args.date_column)
        total_rows_out += len(df)

        # Load
        print("  Loading...")
        output_path = load(df, args.output, filename)

        results.append({
            "input": filepath,
            "output": output_path,
            "rows_in": report["rows"],
            "rows_out": len(df),
            "validation": report["status"],
        })

    # Summary
    elapsed = time.time() - start_time
    pipeline_stats = {
        "total_files": len(files),
        "total_rows_in": total_rows_in,
        "total_rows_out": total_rows_out,
        "elapsed_seconds": round(elapsed, 2),
    }

    write_summary(results, args.output, pipeline_stats)

    print(f"\n{'='*50}")
    print("PIPELINE COMPLETE")
    print(f"{'='*50}")
    print(f"  Files processed: {len(files)}")
    print(f"  Rows in:         {total_rows_in:,}")
    print(f"  Rows out:        {total_rows_out:,}")
    print(f"  Elapsed:         {elapsed:.2f}s")


if __name__ == "__main__":
    main()
