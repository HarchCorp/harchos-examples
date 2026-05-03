# ETL Pipeline on HarchOS

> **Difficulty:** Beginner  
> **Category:** Data Pipelines  
> **Time:** ~15 minutes

## Overview

Build an Extract-Transform-Load (ETL) pipeline that processes CSV data with HarchOS. This example demonstrates:

1. **Extract**: Read raw CSV data from a data source
2. **Transform**: Clean, filter, aggregate, and enrich the data
3. **Load**: Write processed data to Parquet format for downstream consumption

This pattern is useful for data preprocessing before ML training, log analytics, and reporting pipelines.

## Prerequisites

- Python 3.9+
- HarchOS CLI (`pip install harchos`)

## Quick Start

```bash
# Install dependencies
pip install pandas pyarrow harchos

# Run locally
python etl_pipeline.py --input data/raw --output data/processed

# Deploy to HarchOS
harchos workload apply workload.yaml
```

## Pipeline Steps

```
┌──────────┐    ┌──────────────┐    ┌──────────┐    ┌──────────┐
│  Extract  │───►│  Validate    │───►│ Transform │───►│   Load   │
│  (CSV)    │    │  (Schema)    │    │ (Clean)   │    │(Parquet) │
└──────────┘    └──────────────┘    └──────────┘    └──────────┘
```

## Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--input` | /data/raw | Input data directory |
| `--output` | /data/processed | Output directory |
| `--date-column` | date | Column to parse as dates |
| `--chunk-size` | 10000 | Processing chunk size |

## Files

| File | Purpose |
|------|---------|
| `etl_pipeline.py` | Complete ETL pipeline script |
| `workload.yaml` | HarchOS workload manifest |
