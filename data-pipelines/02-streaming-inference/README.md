# Streaming Inference Pipeline on HarchOS

> **Difficulty:** Intermediate  
> **Category:** Data Pipelines  
> **Time:** ~25 minutes

## Overview

Build a streaming inference pipeline that processes data in real-time from a queue, runs ML model inference, and publishes results. This pattern is useful for:

- Real-time classification of incoming data streams
- Continuous inference on event-driven workloads
- Processing IoT sensor data, logs, or user events

## Architecture

```
┌──────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────┐
│  Source   │───►│  Inference   │───►│  Post-process │───►│  Sink    │
│  (Queue)  │    │  (GPU)       │    │  (Enrich)     │    │(Output)  │
└──────────┘    └──────────────┘    └──────────────┘    └──────────┘
```

The pipeline uses a simple file-based queue system for demonstration, but can be adapted to use Redis, Kafka, or any message queue.

## Prerequisites

- Python 3.9+
- HarchOS CLI (`pip install harchos`)

## Quick Start

```bash
# Install dependencies
pip install torch transformers harchos

# Run locally (simulates streaming with sample data)
python streaming_inference.py --model distilbert-base-uncased-finetuned-sst-2-english

# Deploy to HarchOS
harchos workload apply workload.yaml
```

## Files

| File | Purpose |
|------|---------|
| `streaming_inference.py` | Complete streaming inference pipeline |
| `workload.yaml` | HarchOS workload manifest |
